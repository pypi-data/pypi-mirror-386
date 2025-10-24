from pycm import ConfusionMatrix
import matplotlib.pyplot as plt 
import seaborn as sb
import pandas as pd
cf = {
    "Apple":{"Apple":4,"Orange":0,"Cherry":2},
    "Orange":{"Apple":0,"Orange":6,"Cherry":0},
    "Cherry":{"Apple":2,"Orange":0,"Cherry":4}
}

confusion_matrix = ConfusionMatrix(matrix = cf)
print(confusion_matrix)


df = pd.DataFrame(cf).T
plt.figure(figsize=(25,25))
sb.heatmap(df,annot = True,fmt = "d",cmap = "YlGnBu")
plt.title("Actual vs Predicted")
plt.ylabel("Actual")
plt.xlabel("Predicted")
plt.show()

