FROM python:3.7
RUN python -m 
RUN pip install wtforms==2.3.3
RUN pip install --upgrade pip wheel setuptools
RUN pip install dbt-postgres
RUN pip install SQLAlchemy==1.3.23

WORKDIR /dbt
ADD . /dbt
RUN export DBT_PROFILES_DIR= /opt/airflow/dbt