FROM python:3.10
EXPOSE 8501
WORKDIR /app
COPY requirements.txt ./requirements.txt
COPY botocore-1.29.162-py3-none-any.whl ./botocore-1.29.162-py3-none-any.whl
COPY boto3-1.26.162-py3-none-any.whl ./boto3-1.26.162-py3-none-any.whl
COPY awscli-1.27.162-py3-none-any.whl ./awscli-1.27.162-py3-none-any.whl

RUN  pip3 install --upgrade pip && pip3 install -r requirements.txt
RUN  pip3 install botocore-1.29.162-py3-none-any.whl
RUN  pip3 install boto3-1.26.162-py3-none-any.whl
RUN  pip3 install awscli-1.27.162-py3-none-any.whl 
COPY . .

# Command overriden by docker-compose
CMD streamlit run main.py