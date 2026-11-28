FROM public.ecr.aws/lambda/python:3.13

COPY requirements-lambda.txt ${LAMBDA_TASK_ROOT}/requirements.txt

RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY backend/ ${LAMBDA_TASK_ROOT}/backend/
COPY sahana/ ${LAMBDA_TASK_ROOT}/sahana/
COPY knowledge_base/ ${LAMBDA_TASK_ROOT}/knowledge_base/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/lambda_handler.py

CMD ["lambda_handler.handler"]
