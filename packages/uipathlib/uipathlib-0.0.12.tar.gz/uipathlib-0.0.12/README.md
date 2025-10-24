# uipathlib

* [Description](#package-description)
* [Usage](#usage)
* [Installation](#installation)
* [License](#license)

## Package Description

UiPath Cloud client Python package that uses the [requests](https://pypi.org/project/requests/) library.

> [!IMPORTANT]
> This packages uses pydantic~=1.0!

## Usage

* [uipathlib](#uipathlib)

from a script:

```python
import uipathlib

url_base = "https://cloud.uipath.com/my_company/Production/orchestrator_/"
client_id = "ABX"
refresh_token = "ABD"
scope = "OR.Folders.Read OR.Jobs OR.Queues OR.Execution.Read OR.Robots.Read OR.Settings.Read"
fid = "1138055"  # Folder ID (Organization ID)

uipath = uipathlib.UiPath(url_base=url_base,
                          client_id=client_id,
                          refresh_token=refresh_token,
                          scope=scope)
```

```python
# ASSETS
response = uipath.list_assets(fid=fid)
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
# BUCKETS
response = uipath.list_buckets(fid=fid)
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
response = uipath.create_bucket(fid=fid,
                                name="Test 1",
                                guid="f7ea20e9-971b-4c23-9979-321178a68c46",
                                description="Test description 1")
if response.status_code == 201:
    print("Bucket created successfully")
```

```python
bid = "69248"  # bucked id example
response = uipath.delete_bucket(fid=fid, id=bid)
if response.status_code == 204:
    print("Bucket deleted successfully")
```

```python
# UPLOAD
bid = "69243"  # bucked id example
response = uipath.upload_bucket_file(fid=fid,
                                     id=bid,
                                     localpath=r"C:\Users\admin\Desktop\my_bucket_demo.txt",
                                     remotepath=r"my_bucket_demo.txt")
if response.status_code in [200, 201]:
    print("File uploaded successfully")
```

```python
# DELETE
bid = "69243"  # bucked id example
response = uipath.delete_bucket_file(fid=fid,
                                     id=bid, 
                                     filename=r"my_bucket_demo.txt")
if response.status_code == 204:
    print("File deleted successfully")
```

```python
# CALENDARS
response = uipath.list_calendars(fid=fid)
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
# ENVIRONMENTS (UNDER DEVELOPMENT)
response = uipath.list_environments(fid=fid)
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
# JOBS
# Filter examples:
# - "State eq 'Running'"
# - "State eq 'Successful' and ReleaseName eq 'ReleaseNameOrProcessName'"
# - "ReleaseName eq 'ReleaseNameOrProcessName'"
response = uipath.list_jobs(fid=fid, filter="State eq 'Running'")
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
process_key = "ead3e825-7817-426d-8b1d-3991e6eb2809"  # example process key
robot_id = None  # None for default robot, or specify robot ID
response = uipath.start_job(fid=fid,
                            process_key=process_key,
                            robot_id=robot_id)
if response.status_code == 201:
    print(response.content)
```

```python
# MACHINES
response = uipath.list_machines(fid=fid)
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    print(df)
```

```python
# PROCESSES
response = uipath.list_processes(fid=fid)
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
# QUEUES
response = uipath.list_queues(fid=fid)
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
response = uipath.list_queue_items(fid=fid, 
                                   filter="QueueDefinitionId eq 317460")
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
queue_item_id = 1125058579  # example queue item id
response = uipath.get_queue_item(fid=fid,
                                 id=queue_item_id)
if response.status_code == 200:
    df = pd.DataFrame([response.content])
    display(df)  # print(df)
```

```python
queue_name = "RPA_1201_..."  # queue name example
response = uipath.add_queue_item(fid=fid,
                                 queue=queue_name,
                                 data={"EmployeeId": "12345",
                                       "RowId": "566829607423876",
                                       "State": "Approved",
                                       "RequestId": "LR00001",
                                       "Language": "English"},
                                 reference="12345",
                                 priority="Normal")
if response.status_code == 201:
    print(response.content)
```

```python
queue_name = "RPA_1201_..."  # queue name example
queue_item_id = 913233204  # example queue item id
response = uipath.update_queue_item(fid=fid,
                                    queue=queue_name,
                                    id=queue_item_id,
                                    data={"EmployeeId": "54321",
                                          "RowId": "566829607423876",
                                          "State": "Approved",
                                          "RequestId": "LR20001",
                                          "Language": "English"})
if response.status_code == 200:
    print("Queue item updated successfully")
```

```python
queue_item_id = 913233204  # example queue item id
response = uipath.delete_queue_item(fid=fid,
                                    id=queue_item_id)
if response.status_code == 204:
    print("Queue item deleted successfully")
```

```python
# RELEASES
response = uipath.list_releases(fid=fid)
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
# ROBOTS
response = uipath.list_robots(fid=fid)
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
response = uipath.list_robot_logs(fid=fid, filter="JobKey eq a111d111-b111-1f11-b11d-111adac1111d")
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    print(df)
```

```python
# ROLES
response = uipath.list_roles()
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
# SCHEDULES
response = uipath.list_schedules(fid=fid)
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
# SESSIONS
response = uipath.list_sessions(fid=fid)
if response.status_code == 200:
    df = pd.DataFrame(response.content)
    display(df)  # print(df)
```

```python
# Close
del(uipath)
```

## Installation

* [uipathlib](#uipathlib)

Install python and pip if you have not already.

Then run:

```bash
pip install pip --upgrade
```

For production:

```bash
pip install uipathlib
```

This will install the package and all of it's python dependencies.

If you want to install the project for development:

```bash
git clone https://github.com/aghuttun/uipathlib.git
cd uipathlib
pip install -e ".[dev]"
```

To test the development package: [Testing](#testing)

## License

* [uipathlib](#uipathlib)

BSD License (see license file)
