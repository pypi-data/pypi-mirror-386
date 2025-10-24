# Markdown Writer

*Create Markdown documents from within your Python code.*

I recently worked on a data science project in which I had to generate a Markdown report to display interim results from within my Python script. I was unsatisfied by how clunky is felt, particulary to write things like lists. For example, if you want to output a list of bullets from a `list`, you would have to do something like this:

```python
output = ''
for item in my_list:
    output += f"- {item}\n"

# OR
output = "\n".join([f"- {item}" for item in my_list])
```

It gets more complicated (and ugly) very quickly when writing nested lists, and even keeping track of the required number of newline characters takes more effort than it should for such a simple task.

The purpose of this library is to create simple abstractions to make this simple task effortless. To turn your Python `list` into a Markdown list, simply call `md.list(my_list)`.

```python
# Instantiate MarkdownWriter() at the top of your script
md = MarkdownWriter()
# And then build your output step-by-step
md.list(my_list)
```

See [`./examples/example.py`](./examples/example.py) for more examples.

## Features

- Headings
- Lists
  - Numbered lists
  - Nested lists
- Code blocks
- Tables from Pandas DataFrames
- Hyperlinks
- Images
- Saving to File

## Installation
Install with `pip`:
```
pip install python-markdown-writer
```

## Example usage

### Code Block Example

```python
md.code_block('Hello, World!')
```

### Tables from `Pandas`

```python
df = pd.DataFrame({
    "Name": ["Alice", "Bob", "Charlie"],
    "Age": [25, 30, 35],
    "City": ["Cape Town", "Johannesburg", "Durban"]
})
md.table_from_pandas(df)
```

| Name    |   Age | City         |
|:--------|------:|:-------------|
| Alice   |    25 | Cape Town    |
| Bob     |    30 | Johannesburg |
| Charlie |    35 | Durban       |

### List Example

```python
# This is how you create a list:
sports = ["Rugby", "Football", "Cricket"]
md.list(sports)
```

- Rugby
- Football
- Cricket

### Nested List Example

#### Using list levels

A simple way to create nested lists is by specifying the list level.

```python
# This is how you create a nested list:
md.list(["Sports"], level=1)
md.list(["Rugby", "Football", "Cricket"], level=2)
```

- Sports

  - Rugby
  - Football
  - Cricket

#### Using a dictionary

You can also create nested lists from a dictionary.

```python
# This is how you create a nested list from a dictionary:
produce = {
    "Fruits": {
        "Citrus": ["Orange", "Lemon", "Lime"],
        "Berries": ["Strawberry", "Blueberry", "Raspberry"]
    },
    "Vegetables": {
        "Leafy": ["Spinach", "Lettuce"],
        "Root": ["Carrot", "Beetroot"]
    }
}
md.nested_list_from_dict(produce)
```

- Fruits
  - Citrus
    - Orange
    - Lemon
    - Lime
  - Berries
    - Strawberry
    - Blueberry
    - Raspberry
- Vegetables
  - Leafy
    - Spinach
    - Lettuce
  - Root
    - Carrot
    - Beetroot

### Numbered List Example

```python
# This is how you create a numbered list:
sports = ["Rugby", "Football", "Cricket"]
md.numbered_list(sports)
```

1. Rugby
2. Football
3. Cricket

### Image Example

Cape Town is a spectacular city.

```python
md.image(alt_text='Cape Town', url=url)
```

![Cape Town](https://www.go2africa.com/wp-content/uploads/2024/11/Banner--1920x630.jpg)