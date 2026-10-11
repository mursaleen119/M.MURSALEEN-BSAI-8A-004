import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Titanic dataset used as the single shared dataset across weak tasks
url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
df = pd.read_csv(url)
df = df.dropna(subset=["Age", "Sex", "Survived"])

print(df.head())

# Chart 1: Age distribution by survival status
plt.figure(figsize=(9, 6))
sns.histplot(
    data=df,
    x="Age",
    hue="Survived",
    multiple="stack",
    bins=20,
    palette={0: "#9AA7B4", 1: "#D55E00"},
    alpha=0.85
)
plt.title("Age Distribution by Survival Status")
plt.xlabel("Age")
plt.ylabel("Count")
plt.tight_layout()
plt.show()

# Chart 2: Survival rate by class and sex
plt.figure(figsize=(9, 6))
sns.barplot(
    data=df,
    x="Pclass",
    y="Survived",
    hue="Sex",
    palette={"male": "#0072B2", "female": "#D55E00"},
    estimator="mean"
)
plt.title("Survival Rate by Class and Sex")
plt.xlabel("Passenger Class")
plt.ylabel("Survival Rate")
plt.ylim(0, 1)
plt.tight_layout()
plt.show()

print("\nInterpretation: colour and grouping make the main pattern easier to read.")
