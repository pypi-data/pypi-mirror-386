import warnings
warnings.filterwarnings('ignore')
from glob import glob
import pandas as pd
import argparse
import dask
import dask.dataframe as dd
import pyarrow as pa
import numpy as np

from dask.distributed import Client, LocalCluster, wait
import os
import intervals as I
import math
import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
import json
import logging

from dftracer.utils import Indexer, Reader

from dfanalyzer_old.plots import DFAnalyzerPlots

def get_conditions_default(json_obj):
    io_cond = "POSIX" == json_obj["cat"]
    return False, False, io_cond

class DFTConfiguration:
    def __init__(self):
        self.host_pattern = r'corona(\d+)'
        self.rebuild_index = False
        self.batch_size = 1 * 1024 * 1024  # 1 MB
        self.debug = False
        self.verbose = False
        self.workers = 4
        self.log_file = "dfanalyzer.log"
        self.dask_scheduler = None
        self.index_dir = None
        self.time_approximate = True
        self.slope_threshold = 45
        self.time_granularity = 1e6
        self.skip_hostname = True
        self.conditions = None

dft_configuration = DFTConfiguration()

def get_dft_configuration():
    global dft_configuration
    return dft_configuration

def update_dft_configuration(
    host_pattern=None,
    rebuild_index=None,
    batch_size=None,
    debug=None,
    verbose=None,
    workers=None,
    log_file=None,
    dask_scheduler=None,
    index_dir=None,
    time_approximate=None,
    slope_threshold=None,
    time_granularity=None,
    skip_hostname=None,
    conditions=None,
):
    global dft_configuration
    if conditions:
        dft_configuration.conditions = conditions
    if skip_hostname:
        dft_configuration.skip_hostname = skip_hostname
    if host_pattern:
        dft_configuration.host_pattern = host_pattern
    if rebuild_index:
        dft_configuration.rebuild_index = rebuild_index
    if batch_size:
        dft_configuration.batch_size = batch_size
    if debug:
        dft_configuration.debug = debug
    if verbose:
        dft_configuration.verbose = verbose
    if workers:
        dft_configuration.workers = workers
    if log_file:
        dft_configuration.log_file = log_file
    if dask_scheduler:
        dft_configuration.dask_scheduler = dask_scheduler
    if index_dir:
        dft_configuration.index_dir = index_dir
    if time_approximate:
        dft_configuration.time_approximate = time_approximate
    if slope_threshold:
        dft_configuration.slope_threshold = slope_threshold
    if time_granularity:
        dft_configuration.time_granularity = time_granularity
    return dft_configuration


def create_index(filename):
    index_file = f"{filename}.idx"
    if not os.path.exists(index_file):
        indexer = Indexer(filename, index_file, checkpoint_size=32 * 1024 * 1024)
        indexer.build()
        logging.debug(f"Creating index filename={filename}")
    return filename

def generate_batches(filename, max_bytes, batch_size=1 * 1024 * 1024):
    for start in range(0, max_bytes, batch_size):
        # this range is intended since DFTracerJsonLinesBytesReader do
        # line boundary algorithm internally to chop incomplete line
        end = min(start + batch_size, max_bytes)
        logging.debug(f"Created batch filename={filename}, start={start}, end={end}")
        yield filename, start, end

def get_size(filename):
    size = 0
    if filename.endswith('.pfw'):
        size = os.stat(filename).st_size
    elif filename.endswith('.pfw.gz'):
        index_file = f"{filename}.idx"
        indexer = Indexer(filename, index_file)
        size = indexer.get_max_bytes()
    logging.debug(f"File has size filename={filename}, size={size / 1024**3}")
    return filename, int(size)


def load_indexed_gzip_files(filename, start, end):
    index_file = f"{filename}.idx"
    reader = Reader(filename, index_file)
    json_lines = reader.read_line_bytes_json(start, end)
    logging.debug(
        f"Read json lines filename={filename}, start={start}, end={end}, num_lines={len(json_lines)},"
    )
    return json_lines

def load_objects_dict(
    json_dict, fn, time_granularity, time_approximate, condition_fn, load_data
):
    d = {}
    if json_dict is not None:
        try:
            logging.debug(f"Loading dict {json_dict}")
            if "name" in json_dict:
                d["name"] = json_dict["name"]
            if "cat" in json_dict:
                d["cat"] = json_dict["cat"]
            if "pid" in json_dict:
                d["pid"] = json_dict["pid"]
            if "tid" in json_dict:
                d["tid"] = json_dict["tid"]
            if "args" in json_dict and "hhash" in json_dict["args"]:
                d["hhash"] = str(json_dict["args"]["hhash"])
            if "M" == json_dict["ph"]:
                if d["name"] == "FH":
                    d["type"] = 1  # 1-> file hash
                    if (
                        "args" in json_dict
                        and "name" in json_dict["args"]
                        and "value" in json_dict["args"]
                    ):
                        d["name"] = json_dict["args"]["name"]
                        d["hash"] = str(json_dict["args"]["value"])
                elif d["name"] == "HH":
                    d["type"] = 2  # 2-> hostname hash
                    if (
                        "args" in json_dict
                        and "name" in json_dict["args"]
                        and "value" in json_dict["args"]
                    ):
                        d["name"] = json_dict["args"]["name"]
                        d["hash"] = str(json_dict["args"]["value"])
                elif d["name"] == "SH":
                    d["type"] = 3  # 3-> string hash
                    if (
                        "args" in json_dict
                        and "name" in json_dict["args"]
                        and "value" in json_dict["args"]
                    ):
                        d["name"] = json_dict["args"]["name"]
                        d["hash"] = str(json_dict["args"]["value"])
                elif d["name"] == "PR":
                    d["type"] = 5  # 5-> process metadata
                    if (
                        "args" in json_dict
                        and "name" in json_dict["args"]
                        and "value" in json_dict["args"]
                    ):
                        d["name"] = json_dict["args"]["name"]
                        d["hash"] = json_dict["args"]["value"]
                else:
                    d["type"] = 4  # 4-> others
                    if (
                        "args" in json_dict
                        and "name" in json_dict["args"]
                        and "value" in json_dict["args"]
                    ):
                        d["name"] = json_dict["args"]["name"]
                        d["value"] = str(json_dict["args"]["value"])
            else:
                d["type"] = 0  # 0->regular event
                if "dur" in json_dict:
                    dur = json_dict["dur"]
                    if type(dur) is not int:
                        dur = int(dur)
                    ts = json_dict["ts"]
                    if type(ts) is not int:
                        ts = int(ts)
                    d["ts"] = ts
                    d["dur"] = dur
                    d["te"] = d["ts"] + d["dur"]
                    if not time_approximate:
                        d["tinterval"] = I.to_string(
                            I.closed(
                                json_dict["ts"], json_dict["ts"] + json_dict["dur"]
                            )
                        )
                    d["trange"] = int(
                        ((json_dict["ts"] + json_dict["dur"]) / 2.0) / time_granularity
                    )
                d.update(io_function(json_dict, d, time_approximate, condition_fn))
            if fn:
                user_d = fn(json_dict, d, time_approximate, condition_fn, load_data)
                if type(user_d) is list:
                    yield from user_d[1:]
                    d.update(user_d[0])
                else:
                    d.update(user_d)
            logging.debug(f"built an dictionary for line {d}")
            yield d
        except ValueError as error:
            logging.error(f"Processing {json_dict} failed with {error}")
    return {}

def load_objects_str(
    line, fn, time_granularity, time_approximate, condition_fn, load_data
):
    if (
        line is not None
        and line != ""
        and len(line) > 0
        and "[" != line[0]
        and "]" != line[0]
        and line != "\n"
    ):
        try:
            unicode_line = "".join([i if ord(i) < 128 else "#" for i in line])
            json_dict = json.loads(unicode_line, strict=False)
            yield from load_objects_dict(
                json_dict,
                fn,
                time_granularity,
                time_approximate,
                condition_fn,
                load_data,
            )
        except ValueError as error:
            logging.error(f"Processing {line} failed with {error}")
    return {}

def io_function(json_object, current_dict, time_approximate,condition_fn):
    d = {}
    d["phase"] = 0
    if not condition_fn:
        condition_fn = get_conditions_default
    app_io_cond , compute_cond, io_cond = condition_fn(json_object)
    if time_approximate:
        d["total_time"] = 0
        if compute_cond:
            d["compute_time"] = current_dict["dur"]
            d["total_time"] = current_dict["dur"]
            d["phase"] = 1
        elif io_cond:
            d["io_time"] = current_dict["dur"]
            d["total_time"] = current_dict["dur"]
            d["phase"] = 2
        elif app_io_cond:
            d["total_time"] = current_dict["dur"]
            d["app_io_time"] = current_dict["dur"]
            d["phase"] = 3

    else:
        if compute_cond:
            d["compute_time"] = current_dict["tinterval"]
            d["total_time"] = current_dict["tinterval"]
            d["phase"] = 1
        elif io_cond:
            d["io_time"] = current_dict["tinterval"]
            d["total_time"] = current_dict["tinterval"]
            d["phase"] = 2
        elif app_io_cond:
            d["app_io_time"] = current_dict["tinterval"]
            d["total_time"] = current_dict["tinterval"]
            d["phase"] = 3
        else:
            d["total_time"] = I.to_string(I.empty())
            d["io_time"] = I.to_string(I.empty())
    if "args" in json_object:
        if "fhash" in json_object["args"]:
            d["fhash"] = str(json_object["args"]["fhash"])
        if "POSIX" == json_object["cat"] and "ret" in json_object["args"]:
            size = int(json_object["args"]["ret"])
            if size > 0:
                if "write" in json_object["name"]:
                    d["size"] = size
                elif "read" in json_object["name"] and "readdir" not in json_object["name"]:
                    d["size"] = size
        else:
            if "image_size" in json_object["args"]:
                size = int(json_object["args"]["image_size"])
                if size > 0:
                    d["size"] = size
    return d

def io_columns():
    conf = get_dft_configuration()
    return {
        'compute_time': "string[pyarrow]" if not conf.time_approximate else "uint64[pyarrow]",
        'io_time': "string[pyarrow]" if not conf.time_approximate else "uint64[pyarrow]",
        'app_io_time': "string[pyarrow]" if not conf.time_approximate else "uint64[pyarrow]",
        'total_time': "string[pyarrow]" if not conf.time_approximate else "uint64[pyarrow]",
        'fhash': "string[pyarrow]",
        'phase': "uint16[pyarrow]",
        'size': "uint64[pyarrow]"
    }

def group_func(df):
    val = I.empty()
    for index, value in df.items():
        if str(value) != 'NA':
            val = val.union(I.from_string(str(value), int))
    logging.debug(f"Grouped Range into {val}")
    return I.to_string(val)

def union_portions():
    return dd.Aggregation(
        'union_portions',
        chunk=lambda s: s.apply(group_func),
        agg=lambda s: s.apply(group_func)
    )
def difference_portion(df, a, b):
    if str(df[a]) != 'NA' and str(df[b]) != 'NA':
        return I.to_string(I.from_string(str(df[a]), int) - I.from_string(str(df[b]), int))
    elif str(df[a]) != 'NA':
        return df[a]
    else:
        return I.to_string(I.empty())
def size_portion(df, col):
    val = 0.0
    if str(df[col]) == 'NA':
        return val
    ia = I.from_string(str(df[col]), int)
    for i in list(ia):
        if i and not i.is_empty():
            val += i.upper - i.lower
    logging.debug(f"Calculating size of Interval {val}")
    return val
def percentile(n):
    return dd.Aggregation(
        name='percentile_{:02.0f}'.format(n*100),
        # this computes the median on each partition
        chunk=lambda s: s.quantile(n),
        # this combines results across partitions; the input should just be a list of length 1
        agg=lambda s0: s0.quantile(n),
    )
median_fun = dd.Aggregation(
    name="median",
    # this computes the median on each partition
    chunk=lambda s: s.median(),
    # this combines results across partitions; the input should just be a list of length 1
    agg=lambda s0: s0.median(),
)
def human_format(num):
    if num:
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1024:
            magnitude += 1
            num /= 1024.0
        return '{}{}'.format('{:.0f}'.format(num).rstrip('.'), ['', 'KB', 'MB', 'GB', 'TB'][magnitude])
    else:
        return "NA"
def human_format_count(num):
    if num:
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return '{}{}'.format('{:.0f}'.format(num).rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])
    else:
        return "NA"

def human_format_time(num):
    if num:
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            if magnitude < 3:
                magnitude += 1
                num /= 1000.0
            elif magnitude < 5:
                magnitude += 1
                num /= 60
            else:
                magnitude += 1
                num /= 24
                break

        return '{}{}'.format('{:.0f}'.format(num).rstrip('.'), ['us', 'ms', 's','m','hr'][magnitude])
    else:
        return "NA"

class DFAnalyzer:

    def __init__(self, file_pattern, load_fn=None, load_cols={}, load_data = {}, metadata_cols = {}):

        self.conf = get_dft_configuration()
        if self.conf.dask_scheduler:
            client = Client.current()
            if len(load_data)>0:
                client.scatter(load_data)
        file_pattern = glob(file_pattern)
        all_files = []
        pfw_pattern = []
        pfw_gz_pattern = []
        for file in file_pattern:
            if file.endswith('.pfw'):
                pfw_pattern.append(file)
                all_files.append(file)
            elif file.endswith('.pfw.gz'):
                pfw_gz_pattern.append(file)
                all_files.append(file)
            else:
                logging.warning(f"Ignoring unsuported file {file}")
        if len(all_files) == 0:
            logging.error(f"No files selected for .pfw and .pfw.gz")
            exit(1)
        logging.debug(f"Processing files {all_files}")
        delayed_indices = []
        if len(pfw_gz_pattern) > 0:
            dask.bag.from_sequence(pfw_gz_pattern).map(create_index).compute()
        logging.info(f"Created index for {len(pfw_gz_pattern)} files")
        sizes = dask.bag.from_sequence(all_files).map(get_size).compute()
        total_size = sum(size for _, size in sizes)
        logging.info(f"Total size of all files {total_size=}")
        gz_bag = None
        pfw_bag = None
        if len(pfw_gz_pattern) > 0:
            logging.debug(f"Max bytes per file sizes={sizes}")
            json_line_delayed = []
            total_lines = 0
            for filename, max_bytes in sizes:
                total_lines += max_bytes
                for _, start, end in generate_batches(
                    filename, max_bytes, self.conf.batch_size
                ):
                    json_line_delayed.append((filename, start, end))

            logging.info(
                f"Loading batches, num batches={len(json_line_delayed)}, num files={len(pfw_gz_pattern)}, total lines={total_lines}",
            )
            json_line_bags = []
            for filename, start, end in json_line_delayed:
                json_line_bags.append(
                    dask.delayed(load_indexed_gzip_files)(filename, start, end)
                )
            json_lines = dask.bag.concat(json_line_bags)
            gz_bag = json_lines.map(load_objects_dict, fn=load_fn,
                                    time_granularity=self.conf.time_granularity,
                                    time_approximate=self.conf.time_approximate,
                                    condition_fn=self.conf.conditions,
                                    load_data=load_data).flatten().filter(lambda x: "name" in x)
        main_bag = None
        if len(pfw_pattern) > 0:
            pfw_bag = dask.bag.read_text(pfw_pattern).map(load_objects_str, fn=load_fn,
                                                          time_granularity=self.conf.time_granularity,
                                                          time_approximate=self.conf.time_approximate,
                                                          condition_fn=self.conf.conditions,
                                                          load_data=load_data).flatten().filter(lambda x: "name" in x)
        if len(pfw_gz_pattern) > 0 and len(pfw_pattern) > 0:
            main_bag = dask.bag.concat([pfw_bag, gz_bag])
        elif len(pfw_gz_pattern) > 0:
            main_bag = gz_bag
        elif len(pfw_pattern) > 0:
            main_bag = pfw_bag
        if main_bag:
            columns = {'name': "string[pyarrow]", 'cat': "string[pyarrow]",'type': "uint8[pyarrow]",
                       'pid': "uint64[pyarrow]", 'tid': "uint64[pyarrow]", 'hhash': "string[pyarrow]",
                       'ts': "uint64[pyarrow]", 'te': "uint64[pyarrow]", 'dur': "uint64[pyarrow]",
                       'tinterval': "string[pyarrow]" if not self.conf.time_approximate else "uint64[pyarrow]", 'trange': "uint64[pyarrow]"}
            columns.update(io_columns())
            columns.update(load_cols)
            file_hash_columns = {'name': "string[pyarrow]", 'hash':"string[pyarrow]",'pid': "uint64[pyarrow]", 'tid': "uint64[pyarrow]", 'hhash': "string[pyarrow]"}
            hostname_hash_columns = {'name': "string[pyarrow]", 'hash':"string[pyarrow]",'pid': "uint64[pyarrow]", 'tid': "uint64[pyarrow]", 'hhash': "string[pyarrow]"}
            string_hash_columns = {'name': "string[pyarrow]", 'hash':"string[pyarrow]",'pid': "uint64[pyarrow]", 'tid': "uint64[pyarrow]", 'hhash': "string[pyarrow]"}
            other_metadata_columns = { 'name':"string[pyarrow]" ,'value':"string[pyarrow]",'pid': "uint64[pyarrow]", 'tid': "uint64[pyarrow]", 'hhash': "string[pyarrow]"}
            if "FH" in metadata_cols:
                file_hash_columns.update(metadata_cols["FH"])
            if "HH" in metadata_cols:
                hostname_hash_columns.update(metadata_cols["HH"])
            if "SH" in metadata_cols:
                string_hash_columns.update(metadata_cols["SH"])
            if "M" in metadata_cols:
                other_metadata_columns.update(metadata_cols["M"])
            columns.update(file_hash_columns)
            columns.update(hostname_hash_columns)
            columns.update(string_hash_columns)
            columns.update(other_metadata_columns)

            self.all_events = main_bag.to_dataframe(meta=columns)
            events = self.all_events.query("type == 0")
            self.file_hash = self.all_events.query("type == 1")[list(file_hash_columns.keys())].groupby('hash').first().persist()
            self.host_hash = self.all_events.query("type == 2")[list(hostname_hash_columns.keys())].groupby('hash').first().persist()
            self.string_hash = self.all_events.query("type == 3")[list(string_hash_columns.keys())].groupby('hash').first().persist()
            self.metadata = self.all_events.query("type == 4")[list(other_metadata_columns.keys())].persist()
            self.n_partition = math.ceil(total_size / (128 * 1024 ** 2))
            logging.debug(f"Number of partitions used are {self.n_partition}")
            self.events = events.repartition(npartitions=self.n_partition).persist()
            _ = wait(self.events)
            self.events['ts'] = (self.events['ts'] - self.events['ts'].min()).astype('uint64[pyarrow]')
            self.events['te'] = (self.events['ts'] + self.events['dur']).astype('uint64[pyarrow]')
            self.events['trange'] = (self.events['ts'] // self.conf.time_granularity).astype('uint16[pyarrow]')
            self.events = self.events.persist()

            _ = wait([self.file_hash, self.host_hash, self.string_hash, self.metadata, self.events])
        else:
            logging.error(f"Unable to load Traces")
            exit(1)
        logging.info(f"Loaded events")
        self.plots = DFAnalyzerPlots(
            events=self.events,
            slope_threshold=self.conf.slope_threshold,
            time_granularity=self.conf.time_granularity,
        )
        logging.info(f"Loaded plots with slope threshold: {self.conf.slope_threshold}")

    def _calculate_time(self):
        ts_min, te_max = dask.compute(self.events['ts'].min(), self.events['te'].max())
        total_time = te_max - ts_min

        if self.conf.time_approximate:
            grouped_df = self.events.groupby(["trange", "pid", "tid"]) \
                            .agg({"compute_time": sum, "io_time": sum, "app_io_time": sum}) \
                            .groupby(["trange"]).max()
            # check if the max io_time > time_granularity
            max_io_time = grouped_df.max().compute()['io_time']
            if max_io_time > self.conf.time_granularity:
                # throw a warning, running with large granuality
                logging.warning(f"The max io_time {max_io_time} exceeds the time_granularity {self.conf.time_granularity}. " \
                             f"Please adjust the time_granularity to {int(2 * max_io_time /1e6)}e6 and rerun the analyzer.")
            grouped_df["io_time"] = grouped_df["io_time"].fillna(0)
            grouped_df["compute_time"] = grouped_df["compute_time"].fillna(0)
            grouped_df["app_io_time"] = grouped_df["app_io_time"].fillna(0)
            grouped_df["only_compute"] =  grouped_df[["compute_time","io_time"]].apply(lambda s: s["compute_time"] - s["io_time"] if s["compute_time"] > s["io_time"] else 0, axis=1)
            grouped_df["only_io"] =  grouped_df[["compute_time","io_time"]].apply(lambda s: s["io_time"] - s["compute_time"] if s["io_time"] > s["compute_time"] else 0, axis=1)
            grouped_df["only_app_io"] =  grouped_df[["compute_time","app_io_time"]].apply(lambda s: s["app_io_time"] - s["compute_time"] if s["app_io_time"] > s["compute_time"] else 0, axis=1)
            grouped_df["only_app_compute"] =  grouped_df[["compute_time","app_io_time"]].apply(lambda s: s["compute_time"] - s["app_io_time"] if s["compute_time"] > s["app_io_time"] else 0, axis=1)
            final_df = grouped_df.sum().compute()
            total_io_time, total_compute_time, total_app_io_time, \
            only_io, only_compute, only_app_io, only_app_compute = final_df["io_time"], final_df["compute_time"], final_df["app_io_time"], \
                                                                   final_df["only_io"], final_df["only_compute"], final_df["only_app_io"], final_df["only_app_compute"]
        else:
            agg = {"compute_time": union_portions(),
                   "io_time": union_portions(),
                   "app_io_time": union_portions()}
            grouped_df = self.events.groupby("trange").agg(agg, split_out=self.n_partition)
            grouped_df["only_io"] = grouped_df[["io_time", "compute_time"]].apply(difference_portion, a="io_time",
                                                                                  b="compute_time", axis=1,
                                                                                  meta=("string[pyarrow]"))
            grouped_df["only_compute"] = grouped_df[["io_time", "compute_time"]].apply(difference_portion, a="compute_time",
                                                                                       b="io_time", axis=1)
            grouped_df["only_app_io"] = grouped_df[["app_io_time", "compute_time"]].apply(difference_portion, a="app_io_time",
                                                                                  b="compute_time", axis=1,
                                                                                  meta=("string[pyarrow]"))
            grouped_df["only_app_compute"] = grouped_df[["app_io_time", "compute_time"]].apply(difference_portion, a="compute_time",
                                                                                       b="app_io_time", axis=1)
            total_io_time, total_compute_time, total_app_io_time,\
            only_io, only_compute, only_app_io, only_app_compute = dask.compute(
                grouped_df[["io_time"]].apply(size_portion, col="io_time", axis=1).sum(),
                grouped_df[["compute_time"]].apply(size_portion, col="compute_time", axis=1).sum(),
                grouped_df[["app_io_time"]].apply(size_portion, col="app_io_time", axis=1).sum(),
                grouped_df[["only_io"]].apply(size_portion, col="only_io", axis=1).sum(),
                grouped_df[["only_compute"]].apply(size_portion, col="only_compute", axis=1).sum(),
                grouped_df[["only_app_io"]].apply(size_portion, col="only_app_io", axis=1).sum(),
                grouped_df[["only_app_compute"]].apply(size_portion, col="only_app_compute", axis=1).sum(),
            )
        logging.debug(f"Approximate {self.conf.time_approximate} total_time:{total_time}, {total_io_time}, {total_compute_time}, {total_app_io_time}, \
               {only_io}, {only_compute}, {only_app_io}, {only_app_compute}")
        return total_time, total_io_time, total_compute_time, total_app_io_time, \
               only_io, only_compute, only_app_io, only_app_compute

    def _create_interval(self, list_items):
        logging.debug(f"Creating interval from {list_items}")
        prev = list_items[0]
        val = I.closed(prev, prev)
        for proc in list_items[1:]:
            val = val | I.closed(prev, proc)
            prev = proc
        logging.info(f"Created an interval of {val}")
        return val

    def _create_host_intervals(self, hosts_list):
        conf = get_dft_configuration()
        if not conf.skip_hostname:
            logging.debug(f"Creating regex for {hosts_list} {conf.host_pattern}")
            is_first = True
            value = I.empty()
            for host in hosts_list:
                val = int(re.findall(conf.host_pattern, host)[0])
                if is_first:
                    prev = val
                    is_first = False
                    value = I.closed(prev, prev)
                else:
                    value = value | I.closed(prev, val)
            val = re.findall(conf.host_pattern, hosts_list[0])[0]
            regex = hosts_list[0].replace(val, str(value))
            logging.info(f"Created regex value {val}")
        else:
            regex = hosts_list
        return regex

    def _remove_numbers(self, string_items):
        logging.debug(f"Removing numbers from {string_items}")
        item_sets = set()
        for file in string_items:
            item_sets.add(re.sub(r'\d', 'X', str(file)))
        logging.info(f"List after removing numbers {list(item_sets)}")
        return list(item_sets)

    def _check_hosts_time_skew(self):
        # check if there is time skew across nodes
        hosts_ts_df = self.events.groupby('hhash').agg({'ts': 'min'}).compute()
        # filter the hosts if time skew exceeds 30 seconds
        max_time_skew = 30e6
        if np.std(hosts_ts_df['ts']) > max_time_skew:
           logging.warning(f"The time skew exceeds {max_time_skew // 1e6} sec across hosts {hosts_ts_df.index.tolist()}")

    def summary(self):
        num_events = len(self.events)
        logging.info(f"Total number of events in the workload are {num_events}")
        total_time, total_io_time, total_compute_time, total_app_io_time, \
        only_io, only_compute, only_app_io, only_app_compute = self._calculate_time() #(0, 0, 0, 0, 0, 0, 0, 0, 0)
        hosts_used, filenames_accessed, num_procs, compute_tid, posix_tid, io_by_operations = dask.compute(
            self.host_hash["name"].unique(),
            self.file_hash["name"].unique(),
            self.events["pid"].unique(),
            self.events.query("phase == 1")["tid"].unique(),
            self.events.query("phase == 2")["tid"].unique(),
            self.events.query("phase == 2").groupby(["name"]).agg(
                {"dur": [sum, "count"], "size": [sum, "mean", median_fun, min, max, percentile(.25), percentile(.75)]})
        )


        hosts_used = hosts_used.to_list()
        #hosts_used_regex_str = self._create_host_intervals(hosts_used)
        if len(hosts_used) > 1:
            self._check_hosts_time_skew()

        filenames_accessed = filenames_accessed.to_list()
        #filename_basename_regex_str = self._remove_numbers(filenames_accessed)

        num_procs = num_procs.to_list()
        #proc_name_regex = self._create_interval(num_procs)

        io_by_ops_dict = io_by_operations.T.to_dict()

        # Create a new Table object from Rich library
        table = Table(box=None, show_header=False)

        # Add columns to the table for the key and value
        table.add_column(style="cyan")
        table.add_column()
        app_tree = Tree("Scheduler Allocation Details")
        app_tree.add(f"Nodes: {str(len(hosts_used))}") # {hosts_used_regex_str}")
        app_tree.add(f"Processes: {str(len(num_procs))}") # {str(proc_name_regex)}")
        thread_tree = Tree("Thread allocations across nodes (includes dynamically created threads)")
        thread_tree.add(f"Compute: {str(len(compute_tid))}")
        thread_tree.add(f"I/O: {str(len(posix_tid))}")
        app_tree.add(thread_tree)
        app_tree.add(f"Events Recorded: {human_format_count(num_events)}")
        table.add_row("Allocation", app_tree)

        data_tree = Tree("Description of Dataset Used")
        data_tree.add(f"Files: {str(len(filenames_accessed))}") # {filename_basename_regex_str}")
        table.add_row("Dataset", data_tree)

        io_tree = Tree("Behavior of Application")
        io_time = Tree("Split of Time in application")
        io_time.add(f"Total Time: {total_time / 1e6:.3f} sec")
        if total_app_io_time > 0:
            io_time.add(f"Overall App Level I/O: {total_app_io_time / 1e6:.3f} sec")
        if only_app_io > 0:
            io_time.add(f"Unoverlapped App I/O: {only_app_io / 1e6:.3f} sec")
        if only_app_compute > 0:
            io_time.add(f"Unoverlapped App Compute: {only_app_compute / 1e6:.3f} sec")
        if total_compute_time > 0:
            io_time.add(f"Compute: {total_compute_time / 1e6:.3f} sec")
        io_time.add(f"Overall I/O: {total_io_time / 1e6:.3f} sec")
        if only_compute > 0:
            io_time.add(f"Unoverlapped I/O: {only_io / 1e6:.3f} sec")
        if only_compute > 0:
            io_time.add(f"Unoverlapped Compute: {only_compute / 1e6:.3f} sec")
        io_tree.add(io_time)
        padding_size = 6
        key_padding_size = 15
        io_ts = Tree("Metrics by function")
        io_ts.add(
            f"{'Function':<{key_padding_size}}|{'count':<{padding_size}}|{'                  size    ':<{padding_size*6}}     |")
        io_ts.add(
            f"{'':<{key_padding_size}}|{'':<{padding_size}}|{'min':<{padding_size}}|{'25':<{padding_size}}|{'mean':<{padding_size}}|{'median':<{padding_size}}|{'75':<{padding_size}}|{'max':<{padding_size}}|")
        for key, value in io_by_ops_dict.items():
            io_ts.add(
                f"{key.split('.')[-1]:<{key_padding_size}}|{human_format_count(value[('dur', 'count')]):<{padding_size}}|{human_format(value[('size', 'min')]):<{padding_size}}|{human_format(value[('size', 'percentile_25')]):<{padding_size}}|{human_format(value[('size', 'mean')]):<{padding_size}}|{human_format(value[('size', 'median')]):<{padding_size}}|{human_format(value[('size', 'percentile_75')]):<{padding_size}}|{human_format(value[('size', 'max')]):<{padding_size}}|")
        io_tree.add(io_ts)
        # io_ops = Tree("Event count by function")
        # for key, value in io_by_ops_dict.items():
        #     io_ops.add(f"{key.split('.')[-1]} : {value[('dur', 'count')]}")
        # io_tree.add(io_ops)
        table.add_row("I/O Behavior", io_tree)
        console = Console()

        # Print the table with Rich formatting
        console.print(Panel(table, title='Summary'))



def parse_args():
    conf = get_dft_configuration()
    parser = argparse.ArgumentParser(description='DFTracer Analyzer')
    parser.add_argument("trace", type=str,
                        help="Path to trace file from DFTracer. Can contain * for multiple files.")
    parser.add_argument('-d', '--debug', help="Print lots of debugging statements",
                        action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.WARNING)
    parser.add_argument('-v', '--verbose', help="Be verbose", action="store_const", dest="loglevel", const=logging.INFO)
    parser.add_argument("-l","--log-file", default="dfanalyzer_main.log", type=str, help="Logging log file")
    parser.add_argument("-w","--workers", default=conf.workers, type=int, help="Number of dask workers to use")
    parser.add_argument("--dask-scheduler", default=None, type=str, help="Scheduler to use for Dask")
    parser.add_argument("--index-dir", default=None, type=str, help="Scheduler to use for Dask")
    parser.add_argument('-s', '--slope-threshold', default=45, type=int, help='Threshold to determine problematic I/O accesses')
    parser.add_argument('-t', '--time-granularity', default=1e3, type=int, help='Time granularity')
    args = parser.parse_args()
    debug = False
    verbose = False
    if args.loglevel == logging.DEBUG:
        debug = True
    elif args.loglevel == logging.INFO:
        verbose = True
    update_dft_configuration(debug=debug, verbose=verbose, log_file=args.log_file, workers=args.workers, dask_scheduler=args.dask_scheduler,
                             index_dir=args.index_dir, slope_threshold=args.slope_threshold, time_granularity=args.time_granularity)
    return args

def print_versions():
    logging.debug(f"pandas version {pd.__version__}")
    logging.debug(f"dask version {dask.__version__}")
    logging.debug(f"pa version {pa.__version__}")
    logging.debug(f"np version {np.__version__}")


def setup_logging():
    conf = get_dft_configuration()
    loglevel = logging.WARNING
    if conf.verbose:
        loglevel = logging.INFO
    elif conf.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(level=loglevel,
        handlers=[
            logging.FileHandler(conf.log_file, mode="a", encoding='utf-8'),
            logging.StreamHandler()
        ],
        format='[%(levelname)s] [%(asctime)s] %(message)s [%(pathname)s:%(lineno)d]',
        datefmt='%H:%M:%S'
    )

def reset_dask_cluster():
    client = Client.current()
    client.restart()
    logging.info("Restarting all workers")

def setup_dask_cluster():
    conf = get_dft_configuration()
    if conf.dask_scheduler:
        client = Client(conf.dask_scheduler)
        nworkers = len(client.scheduler_info()['workers'])
        update_dft_configuration(workers=nworkers)
        logging.info(f"Initialized Client with {nworkers} workers and link {client.dashboard_link}")
    else:
        cluster = LocalCluster(n_workers=conf.workers)  # Launches a scheduler and workers locally
        client = Client(cluster)  # Connect to distributed cluster and override default
        logging.info(f"Initialized Client with {conf.workers} workers and link {client.dashboard_link}")


def main():
    args = parse_args()
    setup_logging()
    setup_dask_cluster()
    analyzer = DFAnalyzer(args.trace)
    analyzer.summary()
    #analyzer.plots.time_bw_timeline(figsize=(8, 4), time_col="io_time")
    #analyzer.plots.xfer_size_timeline(figsize=(4, 4))

if __name__ == '__main__':
    main()
    exit(0)
