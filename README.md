# Stack Joiner

Nested stacks in AWS CloudFormation provide a way to organize and manage multiple resources as a single unit, making it easier to manage and deploy large and complex infrastructure.

**However**, when stack set with service-managed permissions we can't use them =[

**Nested Stack is not supported in SERVICE_MANAGED permission model**

This package solves this problem, by merging all the stacks in one single file, allowing you to test your infrastructure using nested stacks and making it possible to export them to a single file for deployment


## Installation

```sh
pip install podsearch
```

## Run

```sh
stackjoiner root_template.yaml output.yaml 
```



## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
