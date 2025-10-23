### Project Description

scibite-toolkit - python library for making calls to [SciBite](https://www.scibite.com/)'s TERMite, CENtree, Workbench and SciBite Search.
The library also enables post-processing of the JSON returned from such requests.

## Install

```
$ pip3 install scibite_toolkit
```
Versions listed on [PyPi](https://pypi.org/project/scibite-toolkit/)!

## Example call to TERMite
In this example call to TERMite, we will annotate one zip file from MEDLINE and then process the output to a dataframe with the built in functions of the toolkit.



We will use the first zip file from PubMed's Annual Baseline files.



Two example scripts will be shown - one that authenticates with a SciBite hosted instance of TERMite and one that hosts with a local instance of TERMite (hosted by customer).



*Please note the following:

 you can test with any file. 
If you would like to test with just text (and not a file), please use "t.set_text('your text') and don't use the t.set_binary_content command.

### Example 1 - SciBite Hosted instance of TERMite
```python
import pandas as pd
from scibite_toolkit import termite

# Initialize your TERMite Request
t = termite.TermiteRequestBuilder()

# Specify your TERMite API Endpoint and login URL
t.set_url('url_endpoint')
t.set_saas_login_url('login_url')

# Authenticate with the instance
username = 'username
password = 'password'
t.set_auth_saas(username, password)

# Set your runtime options
t.set_entities('INDICATION')  # comma separated list of VOCabs you want to run over your data
t.set_input_format('medline.xml')  # the input format of the data sent to TERMite
t.set_output_format('json')  # the output format of the response from TERMite
t.set_binary_content('path/to/file')  # the file path of the file you want to annotate
t.set_subsume(True)  # set subsume run time option (RTO) to true

# Execute the request and convert response to dataframe for easy analysis
termite_response = t.execute()
resp_df = termite.get_termite_dataframe(termite_response)
print(resp_df.head(3))
```
### Example 2 - Local Instance of TERMite (Hosted by Customer)

```python
import pandas as pd
from scibite_toolkit import termite

# Initialize your TERMite Request
t = termite.TermiteRequestBuilder()

# Specify your TERMite API Endpoint and login URL
t.set_url('url_endpoint')

# Authenticate with the instance
username = 'username'
password = 'password^'
t.set_basic_auth(username, password)

# Set your runtime options
t.set_entities('INDICATION')  # comma separated list of VOCabs you want to run over your data
t.set_input_format('medline.xml')  # the input format of the data sent to TERMite
t.set_output_format('json')  # the output format of the response from TERMite
t.set_binary_content('path/to/file')  # the file path of the file you want to annotate
t.set_subsume(True)  # set subsume run time option (RTO) to true

# Execute the request and convert response to dataframe for easy analysis
termite_response = t.execute()
resp_df = termite.get_termite_dataframe(termite_response)
print(resp_df.head(3))
```
## Example call to TExpress
In this example call to TExpress, we will annotate one zip file from Medline and then process the output to a dataframe with the built in functions of the toolkit.



We will use the first zip file from PubMed's Annual Baseline files.



Two example scripts will be shown - one that authenticates with a SciBite hosted instance of TExpress and one that authenticates with a local instance of TExpress (hosted by the customer).



Please note the following:

 you can test with any file. 
If you would like to test with just text (and not a file), please use "t.set_text('your text') and don't use the t.set_binary_content command.

### Example 1 - SciBite Hosted Instance of TExpress
```python
import pandas as pd
from scibite_toolkit import texpress

# Initialize your TERMite Request
t = texpress.TexpressRequestBuilder()

# Specify your TERMite API Endpoint and login URL
t.set_url('url_endpoint')
t.set_saas_login_url('login_url')

# Authenticate with the instance
username = 'username'
password = 'password'
t.set_auth_saas(username, password)

# Set your runtime options
t.set_entities('INDICATION')  # comma separated list of VOCabs you want to run over your data
t.set_input_format('medline.xml')  # the input format of the data sent to TERMite
t.set_output_format('json')  # the output format of the response from TERMite
t.set_binary_content('path/to/file')  # the file path of the file you want to annotate
t.set_subsume(True)  # set subsume run time option (RTO) to true
t.set_pattern(':(INDICATION):{0,5}:(INDICATION)')  # pattern to tell TExpress what to look for within data

# Execute the request and convert response to dataframe for easy analysis
texpress_resp = t.execute()
resp_df = texpress.get_texpress_dataframe(texpress_resp)
print(resp_df.head(3))
```
### Example 2 - Local Instance of TExpress (Hosted by Customer)
```python
import pandas as pd
from scibite_toolkit import texpress

# Initialize your TERMite Request
t = texpress.TexpressRequestBuilder()

# Specify your TERMite API Endpoint
t.set_url('url_endpoint')

# Authenticate with the instance
username = 'username'
password = 'password'
t.set_basic_auth(username, password)

# Set your runtime options
t.set_entities('INDICATION')  # comma separated list of VOCabs you want to run over your data
t.set_input_format('pdf')  # the input format of the data sent to TERMite
t.set_output_format('medline.xml')  # the output format of the response from TERMite
t.set_binary_content('/path/to/file')  # the file path of the file you want to annotate
t.set_subsume(True)  # set subsume run time option (RTO) to true
t.set_pattern(':(INDICATION):{0,5}:(INDICATION)')  # pattern to tell TExpress what to look for within data

# Execute the request and convert response to dataframe for easy analysis
texpress_resp = t.execute()
resp_df = texpress.get_texpress_dataframe(texpress_resp)
print(resp_df.head(3))
```
## Example call to SciBite Search

```python
from scibite_toolkit import scibite_search

# First authenticate - The examples provided are assuming our SaaS-hosted instances, adapt accordingly
ss_home = 'https://yourdomain-search.saas.scibite.com/'
sbs_auth_url = "https://yourdomain.saas.scibite.com/"
client_id = "yourclientid"
client_secret ="yourclientsecret"
s = scibite_search.SBSRequestBuilder()
s.set_url(ss_home)
s.set_auth_url(sbs_auth_url)
s.set_oauth2(client_id,client_secret) #Authentication will last according to what was was set up when generating the client

# Now you can use the request object

# Search over documents
sample_query = 'schema_id="clinical_trial" AND (title~INDICATION$D011565 AND DRUG$*)'

# Note that endpoint is capped at 100 results, but you can paginate using the offset parameter
response = s.get_docs(query=sample_query,markup=True,limit=100)

# Co-ocurrence search across sentences
# Get the top 50 co-ocurrence sentence aggregates for psoriasis indication and any gene
response = s.get_aggregates(query='INDICATION$D011565',vocabs=['HGNCGENE'],limit=50)

```
## Example call to Workbench

```python
from scibite_toolkit import workbench
#first authenticate with the instance
username = 'username'
password = 'password'
client_id = 'client_id'
wb = WorkbenchRequestBuilder()
url = 'https://workbench-url.com'
wb.set_oauth2(client_id, username, password)
#then set up your call - here we will be creating a WB dataset, uploading a file to it and annotating it
wb.set_dataset_name = 'My Test Dataset'
wb.set_dataset_desc = 'My Test Description'
wb.create_dataset()
wb.set_file_input('path/to/file.xlsx')
wb.upload_file_to_dataset()
#In this example, we will only annotate two columns with pre-selected VOCabs.
#If you would like to tell WB to annotate the dataset without setting a termite config, just call auto_annotate_dataset
vocabs = [[5,6],[8,9]]
attrs = [200,201]
wb.set_termite_config('',vocabs,attrs)
wb.auto_annotate_dataset()
```

## Example call to CENtree

```python
from scibite_toolkit import centree

# Prepare the request object
# You can obtain your token via your user setting's in the UI or programatically
crb = centree.CentreeRequestBuilder(log_level='CRITICAL')
crb.set_url(centree_url=your_server_url)
crb.set_token(token=token)

# Now you can use the request object to call over the CENTree API methods
# For example, to search for classes:
response = crb.search_classes(query='lung')
```

## License 

Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.
