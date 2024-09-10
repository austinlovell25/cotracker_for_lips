import pandas as pd

df1 = pd.read_csv("/tmp/cotracker_pts_0.csv")
i = 1
try:
    while True:
        df2 = pd.read_csv(f"/home/kwangkim/Projects/cotracker_new/tmp/cotracker_pts_{i}.csv")
        df1 = pd.concat([df1, df2], ignore_index=True)
        i += 1
except:
    df1 = df1.drop(df1.columns[0], axis=1)
    df1.to_csv("cotracker_pts.csv")
