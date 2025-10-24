# LakeBench
[![PyPI Release](https://img.shields.io/pypi/v/lakebench)](https://pypi.org/project/lakebench/)
[![PyPI Downloads](https://img.shields.io/pepy/dt/lakebench.svg?label=PyPI%20Downloads)](https://pypi.org/project/lakebench/)

🌊 LakeBench is the first Python-based, multi-modal benchmarking framework designed to evaluate performance across multiple lakehouse compute engines and ELT scenarios. Supporting a variety of engines and both industry-standard and novel benchmarks, LakeBench enables comprehensive, apples-to-apples comparisons in a single, extensible Python library.

## 🚀 The Mission of LakeBench
LakeBench exists to bring clarity, trust, accessibility, and relevance to engine benchmarking by focusing on four core pillars:
1. **End-to-End ELT Workflows Matter**
    
    Most benchmarks focus solely on analytic queries. But in practice, data engineers manage full data pipelines — loading data, transforming it (in batch, incrementally, or even streaming), maintaining tables, and then querying.

    > LakeBench proposes that **the entire end-to-end data lifecycle managed by data engineers is relevant**, not just queries.

1. **Variety in Benchmarks Is Essential**

    Real-world pipelines deal with with different data shapes, sizes, and patterns. One-size-fits-all benchmarks miss this nuance.

    > LakeBench covers a **variety of benchmarks** that represent **diverse workloads** — from bulk loads to incremental merges to maintenance jobs to ad-hoc queries — providing a richer picture of engine behavior under different conditions.

1. **Consistency Enables Trustworthy Comparisons**

    Somehow, every engine claims to be the fastest at the same benchmark, _at the same time_. Without a standardized framework, with support for many engines, comparisons are hard to trust and even more difficult to reproduce.

    > LakeBench ensures **consistent methodology across engines**, reducing the likelihood of implementation bias and enabling repeatable, trustworthy results. Engine subject matter experts are _encouraged_ to submit PRs to tune code as needed so that their preferred engine is best represented.

1. **Accessibility starts with `pip install`**

    Most benchmarking toolkits are highly inaccessible to the beginner data engineer, requiring the user to build the package or installation via a JAR, absent of Python bindings.

    > LakeBench is intentionally built as a **Python-native library**, installable via `pip` from PyPi, so it's easy for any engineer to get started—no JVM or compilation required. It's so lightweight and approachable, you could even use it just for generating high-quality sample data.


## ✅ Why LakeBench?
- **Multi-Engine**: Benchmark Spark, DuckDB, Polars, Daft, Sail and others, side-by-side
- **Lifecycle Coverage**: Ingest, transform, maintain, and query—just like real workloads
- **Diverse Workloads**: Test performance across varied data shapes and operations
- **Consistent Execution**: One framework, many engines
- **Extensible by Design**: Add engines or additional benchmarks with minimal friction
- **Dataset Generation**: Out-of-the box dataset generation for all benchmarks
- **Rich Logs**: Automatically logged engine version, compute size, duration, estimated execution cost, etc.

LakeBench empowers data teams to make informed engine decisions based on real workloads, not just marketing claims.

## 💪 Benchmarks

LakeBench currently supports four benchmarks with more to come:

- **ELTBench**: An benchmark that simulates typicaly ELT workloads:
  - Raw data load (Parquet → Delta)
  - Fact table generation
  - Incremental merge processing
  - Table maintenance (e.g. OPTIMIZE/VACUUM)
  - Ad-hoc analytical queries
- **[TPC-DS](https://www.tpc.org/tpcds/)**: An industry-standard benchmark for complex analytical queries, featuring 24 source tables and 99 queries. Designed to simulate decision support systems and analytics workloads.
- **[TPC-H](https://www.tpc.org/tpch/)**: Focuses on ad-hoc decision support with 8 tables and 22 queries, evaluating performance on business-oriented analytical workloads.
- **[ClickBench](https://github.com/ClickHouse/ClickBench)**: A benchmark that simulates ad-hoc analytical and real-time queries on clickstream, traffic analysis, web analytics, machine-generated data, structured logs, and events data. The load phase (single flat table) is followed by 43 queries.

_Planned_
- **[TPC-DI](https://www.tpc.org/tpcdi/)**: An industry-standard benchmark for data integration workloads, evaluating end-to-end ETL/ELT performance across heterogeneous sources—including data ingestion, transformation, and loading processes.

## ⚙️ Engine Support Matrix

LakeBench supports multiple lakehouse compute engines. Each benchmark scenario declares which engines it supports via `<BenchmarkClassName>.BENCHMARK_IMPL_REGISTRY`.

| Engine          | ELTBench | TPC-DS | TPC-H   | ClickBench |
|-----------------|:--------:|:------:|:-------:|:----------:|
| Spark (Generic) |    ✅    |   ✅   |   ✅  |    ✅    |
| Fabric Spark    |    ✅    |   ✅   |   ✅  |    ✅    |
| Synapse Spark   |    ✅    |   ✅   |   ✅  |    ✅    |
| HDInsight Spark |    ✅    |   ✅   |   ✅  |    ✅    |
| DuckDB          |    ✅    |   ✅   |   ✅  |    ✅    |
| Polars          |    ✅    |   ⚠️   |   ⚠️  |    🔜    |
| Daft            |    ✅    |   ⚠️   |   ⚠️  |    🔜    |
| Sail            |    ✅    |   ✅   |   ✅  |    ✅    |

> **Legend:**  
> ✅ = Supported  
> ⚠️ = Some queries fail due to syntax issues (i.e. Polars doesn't support SQL non-equi joins, Daft is missing a lot of standard SQL contructs, i.e. DATE_ADD, CROSS JOIN, Subqueries, non-equi joins, CASE with operand, etc.).
> 🔜 = Coming Soon  
> (Blank) = Not currently supported 

## Where Can I Run LakeBench?
Multiple modalities doesn't end at just benchmarks and engines, LakeBench also supports different runtimes and storage backends:

**Runtimes**:
  - Local (Windows)
  - Fabric
  - Synapse
  - HDInsight
  - Google Colab ⚠️

**Storage Systems**:
  - Local filesystem (Windows)
  - OneLake
  - ADLS gen2 (temporarily only in Fabric, Synapse, and HDInsight)
  - S3 ⚠️
  - GS ⚠️

_* ⚠️ denotes experimental storage backends_

## What Table Formats Are Supported?
LakeBench currently only supports Delta Lake.

## 🔌 Extensibility by Design

LakeBench is designed to be _extensible_, both for additional engines and benchmarks. 

- You can register **new engines** without modifying core benchmark logic.
- You can add **new benchmarks** that reuse existing engines and shared engine methods.
- LakeBench extension libraries can be created to extend core LakeBench capabilities with additional custom benchmarks and engines (i.e. `MyCustomSynapseSpark(Spark)`, `MyOrgsELT(BaseBenchmark)`).

New engines can be added via subclassing an existing engine class. Existing benchmarks can then register support for additional engines via the below:

```python
from lakebench.benchmarks import TPCDS
TPCDS.register_engine(MyNewEngine, None)
```

_`register_engine` is a class method to update `<BenchmarkClassName>.BENCHMARK_IMPL_REGISTRY`. It requires two inputs, the engine class that is being registered and the engine specific benchmark implementation class if required (otherwise specifying `None` will leverage methods in the generic engine class)._

This architecture encourages experimentation, benchmarking innovation, and easy adaptation.

_Example:_
```python
from lakebench.engines import BaseEngine

class MyCustomEngine(BaseEngine):
    ...

from lakebench.benchmarks.elt_bench import ELTBench
# registering the engine is only required if you aren't subclassing an existing registered engine
ELTBench.register_engine(MyCustomEngine, None)

benchmark = ELTBench(engine=MyCustomEngine(...))
benchmark.run()
```

---

# Using LakeBench

## 📦 Installation

Install from PyPi:

```bash
pip install lakebench[duckdb,polars,daft,tpcds_datagen,tpch_datagen,sparkmeasure]
```

## Example Usage
To run any LakeBench benchmark, first do a one time generation of the data required for the benchmark and scale of interest. LakeBench provides datagen classes to quickly generate parquet datasets required by the benchmarks.

### Data Generation
- **TPC-H** data generation is provided via the (tpchgen-rs)[https://github.com/clflushopt/tpchgen-rs] project. The project is currently about 10x faster than the next closest method of generating TPC-H datasets. _The TPC-DS version of project is currently under development._
- **TPC-DS** data generation is provided via the DuckDB [TPC-DS](https://duckdb.org/docs/stable/core_extensions/tpcds) extension. The LakeBench wrapper around DuckDB adds support for writing out parquet files with a provided row-group target file size as normally the files generated by DuckDB are atypically small (i.e. 10MB) and are most suitable for ultra-small scale scenarios. LakeBench defaults to target 128MB row groups but can be configured via the `target_row_group_size_mb` parameter of both TPC-H and TPC-DS DataGenerator classes.
- **ClickBench** data is downloaded directly from the Clickhouse host site.

_Generating TPC-H scale factor 1 data takes about 14 seconds on a 2vCore VM._

#### TPC-H Data Generation
```python
from lakebench.datagen import TPCHDataGenerator

datagen = TPCHDataGenerator(
    scale_factor=1,
    target_folder_uri='/lakehouse/default/Files/tpch_sf1'
)
datagen.run()
```

#### TPC-DS Data Generation
```python
from lakebench.datagen import TPCDSDataGenerator

datagen = TPCDSDataGenerator(
    scale_factor=1,
    target_folder_uri='/lakehouse/default/Files/tpcds_sf1'
)
datagen.run()
```

_Notes:_
- TPC-DS data up to SF1000 can be generated on a 32-vCore machine. 
- TPC-H datasets are generated extremely fast (i.e. SF1000 in 20 minutes on an 8-vCore machine).
- The ClickBench dataset (only 1 size) should download with partitioned files in ~ 1 minute and ~ 6 minutes as a single file. 

#### Is BYO Data Supported?
If you want to use you own TPC-DS, TPC-H, or ClickBench parquet datasets, that is fine and encouraged as long as they are to specification. The Databricks [spark-sql-perf](https://github.com/databricks/spark-sql-perf) repo which is commonly used to produce TPC-DS and TPC-H datasets for benchmarking Spark has two critical schema bugs (typos?) in their implementation. Rather than supporting the perpetuation of these typos, LakeBench sticks to the schema defined in the specs. An [issue](https://github.com/databricks/spark-sql-perf/issues/219) was raised for tracking if this gets fixed. These datasets need to be fixed before running LakeBench with any data generated from spark-sql-perf:
1. The `c_last_review_date_sk` column in the TPC-DS `customer` table was named `c_last_review_date` (the **_sk** is missing) and it is generated as a string whereas the TPC-DS spec says this column is a Identity type which would map to a integer. The data value is still a surrogate key but the schema doesn't exactly match the specification.
    _Fix via:_
    ```python
    df = spark.read.parquet(f".../customer/")
    df = df.withColumn('c_last_review_date_sk', sf.col('c_last_review_date').cast('int')).drop('c_last_review_date')
    df.write.mode('overwrite').parquet(f".../customer/")
    ```
1. The `s_tax_percentage` column in the TPC-DS `store` table was named with a typo: `s_tax_precentage` (is "**pre**centage" the precursor of a "**per**centage"??).
    _Fix via:_
    ```python
    df = spark.read.parquet(f"..../store/")
    df = df.withColumnRenamed('s_tax_precentage', 's_tax_percentage')
    df.write.mode('overwrite').parquet(f"..../store/")
    ```

### Fabric Spark
```python
from lakebench.engines import FabricSpark
from lakebench.benchmarks import ELTBench

engine = FabricSpark(
    lakehouse_workspace_name="workspace",
    lakehouse_name="lakehouse",
    lakehouse_schema_name="schema",
    spark_measure_telemetry=True
)

benchmark = ELTBench(
    engine=engine,
    scenario_name="sf10",
    mode="light",
    input_parquet_folder_uri="abfss://...",
    save_results=True,
    result_table_uri="abfss://..."
)

benchmark.run()
```

> _Note: The `spark_measure_telemetry` flag can be enabled to capture stage metrics in the results. The `sparkmeasure` install option must be used when `spark_measure_telemetry` is enabled (`%pip install lakebench[sparkmeasure]`). Additionally, the Spark-Measure JAR must be installed from Maven: https://mvnrepository.com/artifact/ch.cern.sparkmeasure/spark-measure_2.13/0.24_

### Polars
```python
from lakebench.engines import Polars
from lakebench.benchmarks import ELTBench

engine = Polars( 
    schema_or_working_directory_uri = 'abfss://...'
)

benchmark = ELTBench(
    engine=engine,
    scenario_name="sf10",
    mode="light",
    input_parquet_folder_uri="abfss://...",
    save_results=True,
    result_table_uri="abfss://..."
)

benchmark.run()
```
---

## Managing Queries Over Various Dialects

LakeBench supports multiple engines that each leverage different SQL dialects and capabilities. To handle this diversity while maintaining consistency, LakeBench employs a **hierarchical query resolution strategy** that balances automated transpilation with engine-specific customization.

### Query Resolution Strategy

LakeBench uses a three-tier fallback approach for each query:

1. **Engine-Specific Override** (if exists - rare)
   - Custom queries tailored for specific engine limitations or optimizations
   - Example: `src/lakebench/benchmarks/tpch/resources/queries/daft/q14.sql` -> Daft is generally sensitive to multiplying decimals and thus requires casing to `DOUBLE` or managing specific decimal types.

2. **Parent Engine Class Override** (if exists - rare)
   - Shared customizations for engine families, i.e. Spark (_not yet leveraged by any engine and benchmark combinations_).
   - Example: `src/lakebench/benchmarks/tpch/resources/queries/spark/q14.sql`

3. **Canonical + Transpilation** (fallback - common)
   - SparkSQL canonical queries are automatically transpiled via SQLGlot. Each engine registers its `SQLGLOT_DIALECT` constant, enabling automatic transpilation when custom queries aren't needed.
   - Example: `src/lakebench/benchmarks/tpch/resources/queries/canonical/q14.sql`

In all cases, tables are automatically qualified with the catalog and schema if applicable to the engine class.

### Why This Approach?

**Real-World Engine Limitations**: Engines like Daft lack support for `DATE_ADD`, `CROSS JOIN`, subqueries, and non-equi joins. Polars doesn't support non-equi joins. Rather than restricting all queries to the lowest common denominator, LakeBench allows targeted workarounds.

**Automated Transpilation Where Possible**: For most queries, SQLGlot can successfully transpile SparkSQL to engine-specific dialects (DuckDB, Postgres, SQLServer, etc.), eliminating manual maintenance overhead and a proliferation of query variants.

**Expert Optimization**: Engine specific subject matter experts can contribute PRs with optimized query variants that reasonably follow the specification of the benchmark author (i.e. TPC).

### Viewing Generated Queries

To inspect the final query that will be executed for any engine:

```python
benchmark = TPCH(engine=MyEngine(...))
query_str = benchmark._return_query_definition('q14')
print(query_str)  # Shows final transpiled/customized query
```

This approach ensures **consistency** (same business logic across engines), **accessibility** (as much as possible, engines work out-of-the-box), and **flexibility** (custom optimizations where needed).

# 📬 Feedback / Contributions
Got ideas? Found a bug? Want to contribute a benchmark or engine wrapper? PRs and issues are welcome!


# Acknowledgement of Other _LakeBench_ Projects
The **LakeBench** name is also used by two unrelated academic and research efforts:
- **[RLGen/LAKEBENCH](https://github.com/RLGen/LAKEBENCH)**: A benchmark designed for evaluating vision-language models on multimodal tasks.
- **LakeBench: Benchmarks for Data Discovery over Lakes** ([paper link](https://www.catalyzex.com/paper/lakebench-benchmarks-for-data-discovery-over)):
    A benchmark suite focused on improving data discovery and exploration over large data lakes.

While these projects target very different problem domains — such as machine learning and data discovery — they coincidentally share the same name. This project, focused on ELT benchmarking across lakehouse engines, is not affiliated with or derived from either.
