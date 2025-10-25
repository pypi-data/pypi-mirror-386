import time
import pandas as pd
import numpy as np
from typing import List, Optional, Generator, Callable, Any
from rand_engine.main._rand_generator import RandGenerator
from rand_engine.main._constraints_handler import ConstraintsHandler
from rand_engine.file_handlers._writer_batch import FileBatchWriter
from rand_engine.file_handlers._writer_stream import FileStreamWriter
from rand_engine.utils.stream_handler import StreamHandler
from rand_engine.validators.spec_validator import SpecValidator
from rand_engine.validators.exceptions import SpecValidationError

  
class DataGenerator:
      
  def __init__(self, random_spec: Callable[[], dict] | dict, seed: int = None, validate: bool = False):
    # Avalia a spec se for callable

    np.random.seed(seed)
    self.lazy_random_spec = random_spec
    self.lazy_dataframe: Optional[Callable[[], pd.DataFrame]] = None
    self._constraints_db_path = ":memory:"
    # Passa a spec avaliada como callable para manter compatibilidade
    self._size = 1000
    self.write = self._writer()
    self.writeStream = self._stream_writer()
    self._transformers: List[Optional[Callable]] = []
    self.__validate_spec() if validate else None
    self.constraints_handler = ConstraintsHandler(db_path=self._constraints_db_path)
    self._options = {}
 

  def __evaluate_spec(self):
    if callable(self.lazy_random_spec): 
      return self.lazy_random_spec()
    return self.lazy_random_spec
  
  
  def __validate_spec(self):
    evaluated_spec = self.__evaluate_spec()
    SpecValidator.validate_and_raise(evaluated_spec)

  
  def wrapped_df_generator(self, size: int) -> pd.DataFrame:
    """
    This method generates a pandas DataFrame based on random data specified in the metadata parameter.
    :param size: int: Number of rows to be generated.
    :param transformer: Optional[Callable]: Function to transform the generated data.
    :return: pd.DataFrame: DataFrame with the generated data.
    """
    def wrapped_lazy_dataframe():
      evaluated_spec = self.__evaluate_spec()
      constraints = evaluated_spec.get("constraints", {})
      if constraints:
        del evaluated_spec["constraints"]
      rand_generator = RandGenerator(evaluated_spec)
      
      df_pandas = rand_generator.generate_first_level(size=size)
      df_pandas = rand_generator.apply_embedded_transformers(df_pandas)
      df_pandas = rand_generator.apply_global_transformers(df_pandas, self._transformers)
      df_pandas = self.constraints_handler.generate_consistency(df_pandas, constraints)
      return df_pandas
    return wrapped_lazy_dataframe
  

  def transformers(self, transformers: List[Optional[Callable]]):
    self._transformers = transformers
    return self
  

  def size(self, size: int):
    self._size = size
    return self
  

  def checkpoint(self, db_path: str):
    self._constraints_db_path = db_path
    return self


  def option(self, key: str, value: Any):
    if not hasattr(self, "_options"):
      self._options = {}
    self._options[key] = value
    return self


  def get_df(self):
    if self._options.get("reset_checkpoint"):
      self.constraints_handler.delete_state()
    lazy_dataframe = self.wrapped_df_generator(size=self._size)
    assert lazy_dataframe is not None, "You need to generate a DataFrame first."
    return lazy_dataframe()


  def stream_dict(self, min_throughput: int=1, max_throughput: int = 10) -> Generator:
    lazy_dataframe = self.wrapped_df_generator(size=self._size)
    assert lazy_dataframe is not None, "You need to generate a DataFrame first."
    while True:
      df_data_microbatch = lazy_dataframe()
      df_data_parsed = StreamHandler.convert_dt_to_str(df_data_microbatch)
      list_of_records = df_data_parsed.to_dict('records')
      for record in list_of_records:
        record["timestamp_created"] = round(time.time(), 3)
        yield record
        StreamHandler.sleep_to_contro_throughput(min_throughput, max_throughput)
  

  def _writer(self):
    microbatch_def = lambda size: self.wrapped_df_generator(size=size)
    return FileBatchWriter(microbatch_def)
   

  def _stream_writer(self):
    microbatch_def = lambda size: self.wrapped_df_generator(size=size)
    return FileStreamWriter(microbatch_def)



if __name__ == '__main__':

  pass
