import os
import time
from typing import Generator
import uuid
from rand_engine.file_handlers.file_handler import FileHandler
from rand_engine.file_handlers.writer import FileWriter


class FileStreamWriter(FileWriter):


  def __init__(self, microbatch_def):
    super().__init__(microbatch_def)
  

  def trigger(self, frequency: int):
    self.freq = frequency
    return self


  def __handle_filenames(self, path: str, ext: str) -> Generator:
    while True:
      yield f"{path}/part-{str(uuid.uuid4())}.{ext}"

  def __generate_file(self, path):
    dataframe = self.microbatch_def(self._size)
    self.writer_method[self.write_format](dataframe, path, self.write_options)()
    

  def start(self, path):
    base_path, file_name_cleaned, ext = FileHandler.handle_path(path, self.write_format, self.write_options)
    path = f"{base_path}/{file_name_cleaned}"
    os.makedirs(path, exist_ok=True)
    if self.write_mode == "overwrite":
      if os.path.exists(path):
        for f in os.listdir(path):
          os.remove(os.path.join(path, f))
    timeout = self.write_options.get("timeout", 20)
    del self.write_options["timeout"]
    start_time = time.time()
    file_gen = self.__handle_filenames(path, ext)
    for file in file_gen:
      self.__generate_file(file)
      time.sleep(self.freq)
      if time.time() - start_time > timeout: break
