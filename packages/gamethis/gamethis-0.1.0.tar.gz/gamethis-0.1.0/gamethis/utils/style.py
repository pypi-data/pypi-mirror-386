from questionary import Style

# Questionary custom style
custom_style = Style([
    ('qmark', 'fg:#f44336 bold'),       # Question mark
    ('question', 'bold'),               # Question text
    ('pointer', 'fg:#673ab7 bold'),      # Pointer
    ('highlighted', 'fg:#673ab7 bold'),  # Highlighted choice
    ('selected', 'fg:white bg:#673ab7'), # Selected choice
    ('answer', 'fg:#f44336 bold'),      # Answer
])