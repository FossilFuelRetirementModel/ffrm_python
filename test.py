import pandas as pd
# Sample data
data = {
    ('RATNAGIRI', 2021): 9.482040e+07,
    ('RATNAGIRI', 2022): 9.482005e+07,
    ('RATNAGIRI', 2023): 9.481967e+07,
    ('JAYPEE NIGRIE', 2036): 3.524787e+07,
    ('JAYPEE NIGRIE', 2037): 3.396152e+07,
    ('JAYPEE NIGRIE', 2038): 3.247788e+07,
    ('JAYPEE NIGRIE', 2040): -2.157913e+01,
}

# Create a DataFrame from the sample data
df = pd.DataFrame.from_dict(data, orient='index', columns=['Value'])

# Reset the index to create a MultiIndex
df.reset_index(inplace=True)

# Split the tuples into separate columns
df[['Plant', 'Year']] = pd.DataFrame(df['index'].tolist(), index=df.index)

# Set the MultiIndex
df.set_index(['Plant', 'Year'], inplace=True)

# Drop the old index column
df.drop(columns='index', inplace=True)

# Display the transformed DataFrame
print(df)