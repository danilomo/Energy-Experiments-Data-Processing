library(readr)

teste <- read_table2("~/Workspace/Energy-Experiments-Data-Processing/python/teste.csv")

m = lm( power ~ cpu1 , data = teste)

print(summary(m))
