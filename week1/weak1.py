import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Titanic dataset used as the single shared dataset across weak tasks
url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
df = pd.read_csv(url)

print(df.head())
print(df.columns.tolist())
print("Shape:", df.shape)

# Summary table for survival by passenger class
summary = (
    df.groupby("Pclass")["Survived"]
    .agg(["count", "mean"])
    .rename(columns={"count": "Total", "mean": "Survival Rate"})
)
print("\nSummary table:")
print(summary)

# Chart 1: Survival rate by passenger class
plt.figure(figsize=(8, 5))
sns.barplot(
    data=df,
    x="Pclass",
    y="Survived",
    estimator="mean",
    palette="Set2"
)
plt.title("Survival Rate by Passenger Class")
plt.xlabel("Passenger Class")
plt.ylabel("Survival Rate")
plt.ylim(0, 1)
plt.tight_layout()
plt.show()

# Chart 2: Survival rate by sex
plt.figure(figsize=(8, 5))
sns.barplot(
    data=df,
    x="Sex",
    y="Survived",
    estimator="mean",
    palette="pastel"
)
plt.title("Survival Rate by Sex")
plt.xlabel("Sex")
plt.ylabel("Survival Rate")
plt.ylim(0, 1)
plt.tight_layout()
plt.show()

print("\nConclusion: Passenger class and sex both affect survival rate.")
