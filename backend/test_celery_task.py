#!/usr/bin/env python3
from tasks.test_task import add

# Call the task asynchronously
result = add.delay(3, 4)

print(f"Task submitted. Task ID: {result.id}")
