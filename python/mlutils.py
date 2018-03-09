import numpy as np
import pandas as pd
from pandas import DataFrame, Series

def kfold( df, k, bin_ ):
    n = df.shape[0]
    binSize = n // k

    start = (bin_ - 1) * binSize 
    end = bin_ * binSize - 1

    return (df[ [ i >= start and i <= end for i in range(0,n) ] ],
            df[ [ not( i >= start and i <= end ) for i in range(0,n) ] ] )
            
