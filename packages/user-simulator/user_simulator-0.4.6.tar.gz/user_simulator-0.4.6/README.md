# User simulator for chatbot testing

## Description
The evolution of technology increased the complexity of chatbots, and also it's testing methods. With the introduction of LLMs, chatbots are capable of humanizing
conversations and imitating the pragmatics of natural language. Several approaches have been created in order to evaluate the
performance of chatbots. 

The code in this project allows creating test cases based in conversations that a user simulator will have
with the chatbot to test.

## Usage

In order to run the simulator, a specific chatbot should be deployed previously (i.e. Taskyto, Rasa...). 

The script `sensei_chat.py` contains the functions to load the user simulator profile, start a conversation with the chatbot 
and save this conversation and its configuration parámeters. The user simulator profile is stored in yaml files,
which should be located in the project folder created.


## Environment Configuration

In order to install all the necessary packages, execute the requirements.txt file in a virtual environment as:
` pip install -r requirements.txt`. 

Recommended python version: v3.12

Since Sensei is based on LangChain, different LLM providers can be used to run the tests. An API key of the provider
selected must be set as an environment variable, with its corresponding variable name (Ex: OPENAI_API_KEY, GOOGLE_API_KEY...).
For more information about model providers and LangChain, visit the following link: https://python.langchain.com/docs/integrations/chat/



In some cases, an exception could happen while installing the packages. Some troubleshooting carry on are:

- Upgrade pip: `pip install --upgrade pip`
- Upgrade wheel and setuptools: `pip install --upgrade wheel setuptools`

## Initialization

An initialization process is required in order to create a project folder which will contain all information regarding 
the execution of the tests. 

To create this project folder, the script `init_project.py` must be run before anything else along with the command
`--path "project_path" --name "project_name"`. 

Example: `python init_project.py --path C:\your\project\path --name pizza-shop-test`

The project folder will be created following the structure below:
```
project_folder/
    |
    |_ personalities/
    |_ profiles/
    |   |
    |   |_ user profiles (.yml) / user profile folders
    |
    |_ rules/
    |_ types/
    |_ run.yml
```

A project folder contains 5 elements:

- personalities: This folder is used to store the custom personalities created by the user
- profiles: In this folder, all user profiles will be stored as single YAML files or as execution 
folders of YAML files.
- rules: Here, rules for metamorphic testing are disposed.
- types: This folder contains all custom data types created by the user for data input and data extraction.
- run.yml: This file allows the user to create a run configuration instead of creating a whole command line with
execution parameters. This file is structured as follows:
```
project_folder:           # name of the project folder

user_profile:             # name of the user profile YAML to use or name of the folder containing the user profiles.
technology:               # chatbot technology to test (Taskyto, Ada, Kuki, etc.).
connector_params:         # If the chatbot connector contains editable parameters, they can be defined here as a dictionary
output:                   # path where conversation outputs and reports will be stored.
execution_parameters:     # additional execution parameters.
    # - verbose
    # - clean_cache
    # - update_cache
    # - ignore_cache
```

## Execution

To initiate the execution of the test process, it can be done in two ways:

### Command execution

The sensei_chat.py script must be executed along with some command-line arguments for a successful execution.

Example:

```
--technology
taskyto

--connector-params
"base_url=http://localhost,port=5000"

--project-path
C:\path\to\project\folder

--user-profile
profile_1.yaml \\\\\ folder_of_profiles

--output
C:\path\to\extract\output\information

--verbose
```


- --technology: Chatbot technology to test.
- --connector-params: dynamic parameters for the selected chatbot connector
- --project-path: The project path where all testing content is stored for a specific project.
- --user-profile: name of the user profile YAML or the folder containing user profiles to use in the testing process.
- --output: path where conversation outputs and reports will be stored.
- --verbose: shows logs during the testing process.
- --clean-cache: cache is cleaned after the testing process.
- --update-cache: cache is updated with new content if previous cache was saved.
- --ignore-cache: cache is ignored during the testing process.


### run.yml execution

The sensei_chat.py script must be executed with the command --run-from-yaml referencing to a project folder path which contains the
run.yml configuration file explained previously in the "initialization" section.

Once the arguments are assigned inside the run.yml, the execution can be performed.

Example:

`--run-from-yaml examples/academic_helper`

# User Profile YAML Configuration

This file contains all the properties the user will follow in order to carry out the conversation. Since the user simulator is
based in OpenAI GPT4-o LLM technology, some of the fields should be written as prompts in natural language. For these fields, a 
prompt engineering task should be carried out by the tester to narrow down the role of the user simulator and guide its
behaviour. A description of the fields and an example of the YAML structure is described below.

```
test_name: "pizza_order_test_custom"

llm:
  temperature: 0.8
  model: gpt-4o
  model_prov: openai
  format:
    type: text

user:
  language: English
  role: you have to act as a user ordering a pizza to a pizza shop.
  context:
    - personality: personalities/formal-user.yml
    - your name is Jon Doe
  goals:
    - "a {{size}} custom pizza with {{toppings}}"
    - "{{cans}} cans of {{drink}}"
    - how long is going to take the pizza to arrive
    - how much will it cost

    - size:
        function: another()
        type: string
        data:
          - small
          - medium
          - big

    - toppings:
        function: random(rand)
        type: string
        data:
          - cheese
          - mushrooms
          - pepperoni

    - cans:
        function: forward(drink)
        type: int
        data:
          min: 1
          max: 3
          step: 1

    - drink:
        function: forward()
        type: string
        data:
          - sprite
          - coke
          - Orange Fanta

chatbot:
  is_starter: True
  fallback: I'm sorry it's a little loud in my pizza shop, can you say that again?
  output:
    - price:
        type: money
        description: The final price of the pizza order
    - time:
        type: time
        description: how long is going to take the pizza to be ready
    - order_id:
        type: str
        description: my order ID

conversation:
  number: sample(0.2)
  goal_style:
    steps: 5
  interaction_style:
    - random:
      - make spelling mistakes
      - all questions
      - long phrases
      - change language:
          - italian
          - portuguese
          - chinese

```

## test_name

Here it is defined the name of the test suit. This name will be assigned to the exported test file and the folder containing the tests.

## llm
  This parameter establishes the characteristics of the llm model. It consists of a dictionary with two fields, "model" and "temperature".
  - model: This parameter indicates the llm model that will carry out the conversation as the user simulator. Models to use should be available in
LangChain's OpenAI module.
  - model_prov: This optional parameter specifies the model's provider. Sice there are different available providers in LangChain that may
contain the same model, in some cases it is necessary to specify the provider in order to avoid confusion, for example:
    - Gemini models are available in "google-genai" or "google-vertexai" providers.
    - Llama models are available in different providers such as Groq or Fireworks AI.
  - temperature: This parameter controls the randomness and diversity of the responses generated by the LLM. The value supported is float between 0.0 and 1.0.
  - format: This parameter allows the tester to enable the speech recognition module in order to test ASR based chatbots, or
enable the text module to test text chatbots. This parameter contains two sub parameters: "type" and "config". "type" indicates if 
the conversation will use the text module or the speech module, and "config" allows the tester to load a directory to a YAML 
file with the personalized configuration of the speech module. "confing" is only available when "type" is set to "speech" mode.

  
  The whole llm parameter is optional, thus if it is not instantiated in the yaml file, model, temperature and 
  format will be set to default values, which are "gpt-4o", "0.8", and "type: text" respectively.


## user

This field defines the properties of the user simulator in 3 parameters: language, role, context and goals

### language

This parameter defines the main language that will be used in the conversations. If no language is provided, it is set to English by default.

### role

  In this field, the tester should define the role the user will deploy during the conversation as a prompt, according to the chatbot to test.

### context

  This field consist of a list of prompts that will define some characteristics of the user simulator. 
  This can be used to define the name of the user, the availability for an appointment, allergies or intolerances, etc.
  An option for loading predefined "personalities" can be enabled by typing inside of this field "personality:" and the
  path to the YAML file containing the desired personality. These personalities can go along with characteristics added
  by the programmer.

### goals

This field, named "ask_about" in previous versions is used to narrow down the conversation topics the user simulator will carry out with the chatbot. 
It consists of a list of strings and dictionaries.

The tester define a list of prompts with indications for the user simulator to check on the chatbot. 
These prompts can contain variables that should be called inside the text between double brackets {{var}}. 
Variables are useful to provide variability in the testing process and should be instantiated in the list as 
shown in the example above with the exact same name as written between brackets (case-sensitive).

Variables follow a specific structure defined by 3 fields as shown below: data, type and function.
```
goals:
  - "cost estimation for photos of {{number_photo}} artworks"
  - number_photo:
      function: forward()
      type: int
      data:
        step: 2
        min: 1
        max: 6

#      data:             (only with float)
#        steps: 0.2 // linspace: 5 
#        min: 1
#        max: 6
```
  ### type
  This field indicates the type of data that will be substituted in the variable placement.

  Types can be default or custom. Default types are included in Sensei's source code and consist of "string", "int" and 
  "float". Custom types are defined by the user and must be included in the "types" folder inside the project folder.

  Custom types follow the structure in the example below:

```
# Structure for phone_number.yml

name: phone_number
type_description: A phone number
format: r"^\d{3}-\d{7}$"
extraction: str
```

```
# Structure for currency.yml

name: currency
type_description: a float number with a currency
format: r'\d+(?:[.,]\d+)?\s*(?:[\$\€\£]|USD|EUR)'
extraction:
  value:
    type: float
    description: a float value
  currency:
    type: string
    description: a currency unit
```
  - name: indicates the type's name. It must be identical to the name of the yaml file containing the custom type information.
  - type_description: this is a prompt to describe the type created.
  - format: this field defines the format that data will follow in python regular expressions.
  - extraction: The extraction field defines how to extract the relevant data from a matched value based on the format (regex). Its structure depends on the complexity of the extracted information:

    - If the extracted value corresponds directly to a single, basic Python type (e.g. str, int, float), 
    you can simply specify the type name.This means the entire match is returned as a single value of that type, 
    with no further breakdown required.
    - If the extracted value contains multiple meaningful components (e.g. a number and a currency, a date and time, etc.), then the extraction field must define a structured object. 
    Each key represents a component to extract, with its own type and description

  ### data
  Here, the data list to use will be defined. In general, data lists must be defined manually by the user, but there 
  are some cases where it can be created automatically. 

  As shown in the example above, instead of defining a list of the amount of artworks, 
  it is possible to automatically create an integer or float list based on range instructions using a 'min, max, step' structure, 
  where min refers to the minimum value of the list, max refers to the maximum value of the list, 
  and step refers to the separation steps between samples. When working with float data, it can also be used the "linspace" 
  parameter instead of step, where samples will be listed with a linear separation step between them.

  This field also allows the user to create data lists based in prompts by using the function "any()".
```
  - drink:
      function: another()
      type: string
      data:
        - Sprite
        - Coca-Cola
        - Pepsi
        - any(3 soda drinks)
        - any(alcoholic drinks)
```
  By using this function, an LLM creates a list following the instructions provided by the user inside the parenthesis. 
  This function can be used alone in the list or accompanied by other items added by the user. When used with other items,
  the "any()" function will exclude these items from the list generation process in case they're related to the instruction. Multiple
  "any()" functions can be used inside the list.
  Note that if no amount is specified in the prompt, the "any()" function will create a list with an unpredictable amount of items.


  The possibility to add personalized list functions to create data lists is another option available in this field,
  as shown in the example below.

```
  - number:
      function: forward()
      type: int
      data:
        file: list_functions/number_list.py
        function_name: 
        args:
          - 1
          - 6
          - 2

  - pizza_type:
      function: forward()
      type: string
      data:
        file: list_functions/number_list.py
        function_name: shuffle_list
        args: list_functions/list_of_things.yml
```
  In these two examples, a personalized list function is implemented in "data". The structure consist in three parameters:
 - file: The path to the .py file where the function is created
 - function_name: the name of the function to run inside the .py file
 - args: the required input args for the function.

  List functions are fully personalized by the user. 

  ### function
  Functions are useful to determine how data will be added to the prompt.

  Since the data is listed, functions are used to iterate through these lists in order to change the information
  inside the variable in each conversation. The functions available in this update are the following:

- default(): the default() function assigns all data in the list to the variable in the prompt.
- random(): this function picks only one random sample inside the list assigned to the variable.
- random(5): this function picks a certain amount of random samples inside the list. In this example, 5 random 
samples will be picked from the list. This number can't exceed the list length.
- random(rand): this function picks a random amount of random samples inside the list. 
This amount will not exceed the list length.
- another(): the another() function will always randomly pick a different sample until finishing the options.
- another(5): when a certain amount is defined inside the brackets, the another() function will pick this number of
samples without repetition between conversations until finishing the options.
- forward(): this function iterates through each of the samples in the list one by one. It allows to nest multiple
forward() functions in order to cover all combinations possible. To nest forward() functions it is necessary to reference the variable that it is going to nest by typing
its name inside the parenthesis, as shown in the example below:
```
  goals:
    - "{{cans}} cans of {{drink}}"

    - cans:
        function: forward(drink)
        type: int
        data:
          min: 1
          max: 3
          step: 1

    - drink:
        function: forward()
        type: string
        data:
          - sprite
          - coke
          - Orange Fanta

```
- pairwise(): This function iterates through data by creating pairwise based combinations for pairwise testing.Pairwise 
testing is a combinatorial test-design technique that focuses on covering all possible 
pairs of input parameter values at least once. It’s based on the observation that most software faults are triggered 
by interactions of just two parameters, so exercising every pair often finds the majority of bugs 
with far fewer tests than full Cartesian‐product enumeration. 

    The pairwise function must be applied to more than 1 variable in order to create the combinations matrix to iterate. 
Variables will change in each conversation based on the matrix construction. 

## chatbot

  This field provides information about the chatbot configuration and the data to be obtained from the conversation.

### is_starter

  This parameter defines whether the chatbot will start the conversation or not. The value supported is boolean and 
  will be set depending on the chatbot to test. 

### fallback

  Here, the tester should provide the chatbot's original fallback message in order to allow the user simulator to detect 
  fallbacks. This is needed to avoid fallback loops, allowing the user simulator to rephrase the query or change the topic.

### output

This field helps the tester get some certain information for the conversation once it is finished. It is used for data validation tasks.

The tester defines some certain data to obtain from the conversation in order to validate the consistency and
performance of the chatbot. This output field must follow the structure below:

```
  output:
    - price:
        type: currency
        description: The final price of the pizza order
    - time:
        type: time
        description: how long is going to take the pizza to be ready
    - order_id:
        type: string
        description: my order ID
```

A name for the data to output must be defined. Each output must contain these two parameters:

- type: here it is defined the type of value to output. This types can be default or custom as defined in the "type"
parameter in "goals". Default types are the following:
  - int: Outputs data as an integer.
  - float: Outputs data as a float.
  - string: Outputs data as text.
  - time/time("format"): Outputs data in a time format. An output format can be specified by adding a parenthesis with the
desired format written in natural language. Ex: time(UTC), time(hh:mm:ss), time(show time in hours, minutes and seconds)
  - date/time("format"): Outputs data in a date format. Following the same logis as "time" type, a date format can be specified
in natural language. Ex: date(mm/dd/yyyy), date(day-month-year), date(show date in days, months and years)
  - list[type]: Outputs a list of the specified data inside the brackets


- description: In this parameter, the tester should prompt a text defining which information has to be obtained from the conversation.


## conversation

  This field defines some parameters that will dictate how the conversations will be generated. It consists 
  of 3 parameters: number, goal_style and interaction_style.

  ```
conversation:
  number: 3
  max_cost: 1
  goal_style:
    steps: 5
    max_cost: 0.1
  interaction_style:
    - random:
      - make spelling mistakes
      - all questions
      - long phrases
      - change language:
          - italian
          - portuguese
          - chinese
  ```

### number
This parameter specifies the number of conversations to generate. You can assign a specific numeric value to this field to define an exact number of conversations.
Example: number: 2 (This will generate 2 conversations.)

Alternatively, the number of conversations can be determined by the number of combinations derived from the value matrix 
generated by nested forward or pairwise functions—provided these functions are included in the "goals" field.
To use this method, set the number field to "combinations".

- _combinations_:
This option calculates the maximum number of conversations that can be generated based on the total 
number of possible combinations from the value matrices produced only by the forward and pairwise functions. 
The biggest number of combinations obtained by any of the available matrices will be used.
````
conversation:
  number: combinations
````

- _combinations(float)_: 
To reduce the number of conversations, you can specify a percentage by including a float value between 0 and 1 in parentheses.
This value will be used to calculate a proportion of the total number of generated conversations.
````
conversation:
  number: combinations(0.6)  # this will use only 60% of the total conversations.
````

- _combinations(float, function)_:
It is possible to reference the value matrix generated by a specific function to determine the number of conversations 
by including the function's name in parentheses.
````
conversation:
  number: combinations(0.6, pairwise)  # this will use only 60% of the total conversations from the pairwise matrix.
````

````
conversation:
  number: combinations(1, forward)  # this will use the 100% of the total conversations from the biggest forward matrix.
````


### max_cost
Since there is a cost to implementing LLMs, the max_cost parameter has been introduced to keep the expenditure
under control by setting a limit on the cost of the execution. This parameter is optional and the value represents 
price in dollars.

### goal_style
This defines how the conversation should end. There are 3 options in this update
  - steps: the tester should input the number of interactions to be done before the conversation ends.
  - random steps: a random number of interactions will be done between 1 and an amount defined by the user. This amount can't exceed 20.
  - all_answered: the conversation will end as long as all the queries in "goals" have been asked by the user and answered by the chatbot. 
  This option creates an internal data frame that verifies if all "goals" queries are being responded or confirmed, and it is possible to export this
  dataframe once the conversation ended by setting the "export" field as True, as shown in the following example. This field is not mandatory, thus if only
  "all_answered" is defined, the export field is set as False by default.
    When all_answered is set, conversations are regulated with a loop break based on the chatbot's fallback message in order to avoid infinite loops when the chatbot does 
  not know how to answer to several questions made by the user. But, in some cases, this loop break can be dodged due to hallucinations from the chatbot, leading to
  irrelevant and extremely long conversations. To avoid this, a "limit" parameter is implemented in order to give the tester the possibility to stop the conversation
  after a specific amount of interactions in case the loop break was not triggered before or all queries were not answered. This parameter is not mandatory neither and will
  be set to 30 interactions by default.
  ```
  goal_style:
    all_answered:
      export: True
      limit: 20
  ```
  - default: the default mode enables "all_answered" mode with 'export' set as False and 'limit' set to 30, since no steps are defined.
  - max_cost (individual): This parameter mimics the functionality of the max_cost parameter defined a level above. However, the
cost limit is set fot each individual conversation inside the execution. Once this limit is surpassed, the conversation ends
and the next one is executed. This parameter is optional, but when used, it must be defined in conjunction with the goal 
styles explained before.
  ```
conversation:
  number: sample(0.2)
  max_cost: 1           # cost limit per execution
  goal_style:
    steps: 5
    max_cost: 0.1       # cost limit per conversation
  ```

### interaction_style
This indicates how the user simulator should carry out the conversation. There are 7 options in this update
  - long phrase: the user will use very long phrases to write any query.
  - change your mind: the user will change its mind eventually. Useful in conversations when the user has to
                      provide information, such as toppings on a pizza, an appointment date...
  - change language: the user will change the language in the middle of a conversation. This should be defined as a list
                     of languages inside the parameter, as shown in the example above.
  - make spelling mistakes: the user will make typos and spelling mistakes during the conversation
  - single question: the user makes only one query per interaction from "goals" field.
  - all questions: the user asks everything inside the "goals" field in one interaction.
  - random: this options allows to create a list inside of it with any of the interaction styles mentioned above. 
Then, it selects a random amount of interaction styles to apply to the conversation. Here's an example on how to apply this interaction style:
    ```
    interaction_style:
      - random:
        - make spelling mistakes
        - all questions
        - long phrases
        - change language:
            - italian
            - portuguese
            - chinese
    ```
  - default: the user simulator will carry out the conversation in a natural way.




# Profile Validation

The validation_check.py script enables testers to carry out a validation process on the generated profile.
It produces two types of output files: a JSON file that reports any formatting errors detected in the 
profile, and CSV files containing the matrices generated by the functions utilized within the profile.

![img.png](data%2Freadme_data%2Fimg.png)

The script contains the following run arguments:

- --profile: Specifies the directory containing the profile to be validated.
- --output: Defines the path where the output files will be saved.
- --combined-matrix: If enabled, generates a single combined matrix of all function elements instead of separate matrices for each function.
- --verbose: Displays detailed logs of the validation process.

Example:
`--profile path\to\profile.yml --export export\path --combined_matrix --verbose`


  
