require(nnet)
require(readr)
library(tictoc)

load("/home/danilo/Workspace/Energy-Experiments-Data-Processing/R/workspace.RData")

args = commandArgs(trailingOnly=TRUE)

nneurons = as.numeric(args[1])


normalizeVec <- function(x){
  return ( (x-min(x))/(max(x)-min(x)) )
}

normalizeDf <- function(d){
  df = data.frame(d)
  df$cpunorm = normalizeVec(df$cpu1)
  df$ionorm = normalizeVec(df$io)
  df$netnorm = normalizeVec(df$net)
  
  return(df)
}

process <- function(d){
  df = data.frame(d)
  df$io = df$io_write + df$io_read
  df$net = df$net_up + df$net_down
  return(df)
}


fastmerge <- function(d1, d2) {
  d1.names <- names(d1)
  d2.names <- names(d2)
  
  # columns in d1 but not in d2
  d2.add <- setdiff(d1.names, d2.names)
  
  # columns in d2 but not in d1
  d1.add <- setdiff(d2.names, d1.names)
  
  # add blank columns to d2
  if(length(d2.add) > 0) {
    for(i in 1:length(d2.add)) {
      d2[d2.add[i]] <- NA
    }
  }
  
  # add blank columns to d1
  if(length(d1.add) > 0) {
    for(i in 1:length(d1.add)) {
      d1[d1.add[i]] <- NA
    }
  }
  
  return(rbind(d1, d2))
}

kfold <- function( df, k, bin ){
  n = nrow(df)
  binSize = n  %/% k
  indexes = c( (bin - 1) * binSize + 1, bin * binSize)
  
  if(bin == 1){
    testing = df[indexes[1]:indexes[2],]
    training = df[(indexes[2] + 1):n,]
  }else if(bin == k){
    training = df[1:(indexes[1]-1),]
    testing = df[indexes[1]:n,]
  }else{
    testing = df[indexes[1]:indexes[2],]
    t1 = df[1:(indexes[1]-1),]
    t2 = df[(indexes[2] + 1):n,]
    training = fastmerge(t1, t2)
  }
  
  return(list(testing, training))
}

percentualError <- function(model, test, realValue){
  pred = predict(model, test)
  
  error = abs(realValue - pred * 200)
  
  (error / realValue) * 100
}

kfoldcrossvalidation <- function(df, generateModel, k){
  
  errors = list()
  
  for(i in 1:k){
    l = kfold( df, k, i)
    test = l[[1]]
    training = l[[2]]
    
    perror = percentualError(generateModel(training), test, test$power)
    errors = c(errors, mean(perror))
  }
  
  return(unlist(errors))
}


neuralNetGenerator <- function(i){
  return(
    function(df){
      nnet(power/200 ~ cpunorm + netnorm + ionorm , data=df, size=i, maxit=12000, trace = F) 
    }
  )
}

regressionGen <- function(df){
  return(lm( power ~ cpunorm + I(cpunorm^2) + I(cpunorm^3) + I(cpunorm^4) + ionorm + I(ionorm^2) + I(ionorm^3) + I(ionorm^4) + netnorm + I(netnorm^2) + I(netnorm^3) + I(netnorm^4), data = df ))
}

#logall <- read_delim("~/Desktop/pendrive/processing/logs/logall.csv",
#                     " ", escape_double = FALSE, trim_ws = TRUE)
log1 = normalizeDf(process(logall))
df = log1[sample(1:nrow(log1)), ]

k = 10

f <- function(i){
  l = kfold( df, k, i)
  test = l[[1]]
  training = l[[2]]

  tic("Rona")
  m = gen(df)
  x = toc()
  print(x)
  
  perror = percentualError( m, test, test$power)
  #return(mean(perror))
  t = (x$toc - x$tic)[[1]]

  return(t)
}

library(parallel)

maxNeurons = 10

neurons = 1:maxNeurons
meanErr = rep(0, maxNeurons)
lowerConf = rep(0, maxNeurons)
highConf = rep(0, maxNeurons)

resultDf = data.frame( neurons, meanErr, lowerConf, highConf)

for( i in 10:10){
  
  gen = neuralNetGenerator(i)
  
  cl <- makeCluster(8)
  
  clusterExport(cl, "gen")
  clusterExport(cl, "percentualError")
  clusterExport(cl, "df")
  clusterExport(cl, "k")
  clusterExport(cl, "nnet")
  clusterExport(cl, "kfold")
  clusterExport(cl, "fastmerge")
  clusterExport(cl, "nneurons")
  clusterExport(cl, "i")
  clusterExport(cl, "tic")
  clusterExport(cl, "toc")
  
  
  l =  parLapply( cl, 1:8, f )
  
  err = unlist(l)
  tTestResult = t.test(err)
  r = c( i, mean(err), tTestResult[[4]][1], tTestResult[[4]][2])
  
  print(r)
  
  stopCluster(cl)
}
