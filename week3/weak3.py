import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Titanic dataset used as the single shared dataset across weak tasks
url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
df = pd.read_csv(url)
df = df.dropna(subset=["Age", "Sex", "Pclass"])

print(df.head())

# Bad example: valid but weak chart
plt.figure(figsize=(9, 6))
sns.boxplot(
    data=df,
    x="Pclass",
    y="Age",
    hue="Sex",
    palette="Set2"
)
plt.title("BAD EXAMPLE: Age by Class and Sex")
plt.xlabel("Passenger Class")
plt.ylabel("Age")
plt.tight_layout()
plt.show()

# Honest redesign
plt.figure(figsize=(9, 6))
sns.boxplot(
    data=df,
    x="Pclass",
    y="Age",
    hue="Sex",
    palette={"male": "#0072B2", "female": "#D55E00"},
    dodge=True
)
plt.title("Age Distribution by Class and Sex")
plt.xlabel("Passenger Class")
plt.ylabel("Age")
plt.tight_layout()
plt.show()

# Mechanism chart: average fare by class and survival
fare_summary = (
    df.groupby(["Pclass", "Survived"])["Fare"]
    .mean()
    .reset_index()
)

plt.figure(figsize=(9, 6))
sns.barplot(
    data=fare_summary,
    x="Pclass",
    y="Fare",
    hue="Survived",
    palette={0: "#9AA7B4", 1: "#D55E00"}
)
plt.title("Average Fare by Class and Survival")
plt.xlabel("Passenger Class")
plt.ylabel("Average Fare")
plt.tight_layout()
plt.show()

print("\nConclusion: the chart must expose the real mechanism clearly instead of just looking valid.")
