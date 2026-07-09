from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="tourinsight_weather_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["tourinsight", "weather"]
) as dag:

    extract_weather = BashOperator(
        task_id="extract_weather",
        bash_command="cd /opt/airflow && python etl/weather/extract_weather.py"
    )

    transform_weather = BashOperator(
        task_id="transform_weather",
        bash_command="cd /opt/airflow && python etl/weather/transform_weather.py"
    )

    load_weather = BashOperator(
        task_id="load_weather_to_neon",
        bash_command="cd /opt/airflow && python etl/weather/load_weather_to_neon.py"
    )
    
    extract_weather >> transform_weather >> load_weather