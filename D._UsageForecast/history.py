# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

# from IPython import parallel
# clients = parallel.Client(profile='ssh-ipy2.0')
# clients.block = True  # use synchronous computations
# print clients.ids

# <codecell>

#%%px
%matplotlib inline
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

#Load original data
data = pd.read_csv('popularity-728days_my.csv')

head = list(data.columns[:21]) + range(1,105)
data = pd.DataFrame(columns=head, data=data.values)

# <codecell>

#%%px
#Select data
selection = ((data['Now'] - data['Creation-week']) > 26)&((data['Now'] - data['FirstUsage']) > 26)&((data[78] - data[1]) != 0)
data_sel = data[selection].copy()
#data_sel = data.copy()
print data_sel.shape

# <codecell>

#%%px
periods = range(1,105)

#------------------------------------------------------
#Get maximum intervals and last weeks with zeros usages
def InterMax(data_sel, periods):
    #Get binary vector representation of the selected data
    data_bv = data_sel.copy()
    #Get week's usages
    for i in periods:
        if i!=1:
            data_bv[i] = data_sel[i] - data_sel[i-1]
            
    #Get binary representation
    data_bv[periods] = (data_bv[periods] != 0)*1
    
    inter_max = []
    last_zeros = []
    nb_peaks = []
    inter_mean = []
    inter_std = []
    inter_rel = []
    
    for i in range(0,data_bv.shape[0]):
        ds = data_bv[periods].irow(i)
        nz = ds.nonzero()[0]
        inter = []
        
        nb_peaks.append(len(nz))
        if len(nz)==0:
            nz = [0]
        if len(nz)<2:
            inter = [0]
            #nz = [0]
        else:
            for k in range(0, len(nz)-1):
                val = nz[k+1]-nz[k]
                inter.append(val)
        
        inter = np.array(inter)
        inter_mean.append(inter.mean())
        inter_std.append(inter.std())
        if inter.mean()!=0:
            inter_rel.append(inter.std()/inter.mean())
        else:
            inter_rel.append(0)
                
        last_zeros.append(periods[-1] - nz[-1] + 1)
        inter_max.append(max(inter))
    
    return np.array(inter_max), np.array(last_zeros), np.array(nb_peaks), np.array(inter_mean), np.array(inter_std), np.array(inter_rel)

# <codecell>

#%%px
#Add features
inter_max, last_zeros, nb_peaks, inter_mean, inter_std, inter_rel = InterMax(data_sel, periods)
data_sel['last-zeros'] = last_zeros
data_sel['inter_max'] = inter_max
data_sel['nb_peaks'] = nb_peaks
data_sel['inter_mean'] = inter_mean
data_sel['inter_std'] = inter_std
data_sel['inter_rel'] = inter_rel

# <codecell>

#%%px
data = data_sel[data_sel['nb_peaks']>=0]

# <codecell>

#%%px
data_weeks = data[range(1,105)]

# <codecell>

#%%px
df_time_series = data_weeks.copy()
for i in range(1,105):
    if i!=1:
        df_time_series[i] = data_weeks[i]-data_weeks[i-1]

# <codecell>

#%%px
param1 = 13
df_ts_rolling_sum = pd.rolling_sum(df_time_series, window=param1,axis=1)[range(param1,105)]

# <codecell>

def smoothing2(serie):
    serie = pd.ewma(serie, com=1)
    serie = pd.ewma(serie, com=1)
    serie = pd.ewma(serie, com=1)
    serie = pd.ewma(serie[::-1], com=1)[::-1]
    serie = pd.ewma(serie[::-1], com=1)[::-1]
    serie = pd.ewma(serie[::-1], com=1)[::-1]
    return serie

# <codecell>

#df_ts_rolling_sum[range(param1, 105-23)] = df_ts_rolling_sum[range(param1, 105-23)].apply(smoothing2, axis=1)

# <codecell>

df_ts_rolling_sum

# <codecell>

param3 = 105-param1

# <codecell>

def smoothing(time_serie):
    serie = time_serie.values[0]
    serie = pd.ewma(serie, com=1)
    serie = pd.ewma(serie, com=1)
    serie = pd.ewma(serie, com=1)
    serie = pd.ewma(serie[::-1], com=1)[::-1]
    serie = pd.ewma(serie[::-1], com=1)[::-1]
    serie = pd.ewma(serie[::-1], com=1)[::-1]
    sm_serie = pd.DataFrame(data=[serie], columns=time_serie.columns)
    return sm_serie

# <codecell>

# %%px
results = pd.DataFrame(columns=["Index","Error_train","Error_valid", "Error_test"]+range(0,param3))
# results.to_csv('/mnt/w76/notebook/datasets/mikhail/ann_res.csv')

# <codecell>

from sklearn.linear_model import LinearRegression, Ridge, Lasso, Lars, OrthogonalMatchingPursuit, PassiveAggressiveRegressor, Perceptron
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import PolynomialFeatures
from sklearn.isotonic import IsotonicRegression
from sklearn.svm import SVR

poly = PolynomialFeatures(degree=1)
lr = LinearRegression()
#lr = SVR()
#lr = Ridge(alpha=0.5)
#lr = Lasso(alpha=0.02)
#lr = OrthogonalMatchingPursuit()
#lr = Lars()
#lr = PassiveAggressiveRegressor()
#lr = IsotonicRegression(increasing='auto')

# <codecell>

t=13
v=10
param4 = v+t

def ANN(rows_range):
    
    keys = [i for i in range(1,param3+1)]
    results = pd.DataFrame(columns=["Index","Error_train","Error_valid", "Error_test"]+keys)

    for row in rows_range:
        if row%500==0:
            print row
        #Take a row and transfrom it
        ts_train = df_ts_rolling_sum.irow([row])
        index = ts_train.index[0]
        max_value = ts_train.max(axis=1).values[0]
        ts_train = ts_train/(1.0*max_value)
        x = np.array([[float(i)/105.] for i in range(0, 105)])
        #Get train data
        x_train = x[range(param1, 105-param4)]
        y_train = ts_train[range(param1, 105-param4)].values[0]
        y_train = y_train.reshape(len(y_train),1)
        #Get validation data
        x_valid = x[range(105-param4, 105-param4+v)]
        y_valid = ts_train[range(105-param4, 105-param4+v)].values[0]
        y_valid = y_valid.reshape(len(y_valid),1)
        #Get test data
        x_test = x[range(105-param4+v, 105)]
        y_test = ts_train[range(105-param4+v, 105)].values[0]
        y_test = y_test.reshape(len(y_test),1)
        #Add new features
        
        # Create network with 2 layers and random initialized
#         lr.fit(poly.fit_transform(x_train), y_train)

#         # Simulate network
#         out_train = lr.predict(poly.fit_transform(x_train))
#         out_valid = lr.predict(poly.fit_transform(x_valid))
#         out_test = lr.predict(poly.fit_transform(x_test))
        
        lr.fit(x_train, y_train)

        # Simulate network
        out_train = lr.predict(x_train)
        out_valid = lr.predict(x_valid)
        out_test = lr.predict(x_test)

#         plt.subplot(1,1,1)
#         plt.plot(np.concatenate((y_train,y_valid, y_test),axis=0), color='b')
#         plt.plot(np.concatenate((out_train,out_valid,out_test),axis=0), color='r')
#         plt.ylim(-1,1.5)
#         plt.show()


        #Get results
        #index = ts_train.index[0]
        error_train = mean_absolute_error(y_train, out_train)
        error_valid = mean_absolute_error(y_valid, out_valid)
        error_test = mean_absolute_error(y_test, out_test)
        values = list(np.concatenate((out_train,out_valid,out_test)))
        values = np.reshape(values,(len(values),))
        data_dict = {"Index":[index],"Error_train":[error_train],"Error_valid":[error_valid], "Error_test":[error_test]}
        for i in range(1,param3+1):
            data_dict[i] = [values[i-1]]
        new_row = pd.DataFrame(data=data_dict)
        results = results.append(new_row)
        
    #results.to_csv('/mnt/w76/notebook/datasets/mikhail/ann_res.csv',mode='a',header=False)
    return results

# <codecell>

#%%px
#!easy_install neurolab

# <codecell>

rows = range(0,5704)#5704

# <codecell>

%%time
results = ANN(rows)

# <codecell>

import pandas as pd
results.to_csv('res.csv')

# <codecell>

a = results[val_cols].irow([0]).values[0]
plt.plot(a)
plt.show()

# <codecell>

%matplotlib inline
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

results = pd.read_csv('res.csv')
results.columns

# <codecell>

results['nb_peaks'] = [data['nb_peaks'].ix[int(i)] for i in results['Index'].values]
results['inter_max'] = [data['inter_max'].ix[int(i)] for i in results['Index'].values]

# <codecell>

df_ts_rolling_sum.columns
#df_ts_rolling_sum = (df_ts_rolling_sum>0)*1

# <codecell>

val_cols = [i for i in range(1,105-param3)]  
non_nan_res = results[(pd.isnull(results).sum(axis=1)==0)*(results['Error_valid']<=2)*(results['Error_train']<=2)]
#non_nan_res[val_cols] = (non_nan_res[val_cols].values>=0.95)*1
non_nan_res.shape

# <codecell>

max_values = df_ts_rolling_sum.max(axis=1)
df_ts_rolling_sum_std = df_ts_rolling_sum.copy()
for col in df_ts_rolling_sum.columns:
    df_ts_rolling_sum_std[col] = df_ts_rolling_sum[col]/max_values

# <codecell>

non_nan_res[val_cols].irow([0]).values[0]

# <codecell>

val_cols = [i for i in range(1,105-param1+1)]
val_x = range(param1,105)
cols = range(param1,105)
a=0
b=60
N=b-a
figure(figsize=(15, 5*(N//3+1)))
for row in range(a,b):
    subplot(N//3+1,3,row)
    plt.plot(val_x,non_nan_res[val_cols].irow([row]).values[0], color='r', label='predict')
    index = int(non_nan_res.irow([row])['Index'].values)
    plt.plot(cols, df_ts_rolling_sum_std[cols].xs(index), color='b', label='real')
    plt.plot([105-t,105-t], [-1,1], color='black')
    plt.plot([105-v-t,105-v-t], [-1,1], color='black')
    plt.title('Index is '+str(index))
    #plt.xlim(ws,105)
    plt.ylim(-1,1.1)
    plt.legend(loc='best')
    #plt.show()

# <codecell>

#print error hists
figure(figsize=(15, 5))
subplot(121)
plt.hist(non_nan_res['Error_test'].values, color='r', bins=20, label='test', alpha=1, histtype='step')
plt.hist(non_nan_res['Error_train'].values, color='b', bins=20, label='train', alpha=1, histtype='step')
plt.hist(non_nan_res['Error_valid'].values, color='g', bins=20, label='valid', alpha=1, histtype='step')
plt.title('Errors')
plt.legend(loc='best')
#plt.show()

#print predict value for the last point
subplot(122)
plt.hist(non_nan_res[str(param3)].values, bins=10, label='last point')
plt.title('Predict values')
plt.legend(loc='best')
#plt.show()

# <codecell>

y_last=[]
y_valid_last = []
for i in non_nan_res['Index']:
    i=int(i)
    cur_serie = df_ts_rolling_sum.xs(i).values
    y_last.append(cur_serie[param3-10]/(1.0*cur_serie.max()))
    y_valid_last.append(cur_serie[param3-v-t]/(1.0*cur_serie.max()))
y_last = np.array(y_last)
y_valid_last = np.array(y_valid_last)

# <codecell>

non_nan_res[y_last<=0.001].shape

# <codecell>

figure(figsize=(15, 10))
#print predict value for the last point
subplot(2,2,1)
values = non_nan_res[str(param3)].values
plt.hist(values[y_last<=0.001], bins=10, label='y_last=0', alpha=0.5)
plt.hist(values[y_last>0.001], bins=10, label='y_last!=0', alpha=0.5)
plt.title('Predict values')
plt.legend(loc='best')
#plt.show()

#print predict value for 66th week
subplot(2,2,2)
values = non_nan_res['Error_test'].values
plt.hist(values[y_last<=0.001], bins=10, label='y_last=0', alpha=0.5)
plt.hist(values[y_last>0.001], bins=10, label='y_last!=0', alpha=0.5)
plt.title('Error_test')
plt.legend(loc='best')
#plt.show()

#print predict value for 66th week
subplot(2,2,3)
values = non_nan_res['Error_valid'].values/(non_nan_res[str(param3)].values+2.0)
plt.hist(values[y_last<=0.001], bins=10, label='y_last=0', alpha=0.5)
plt.hist(values[y_last>0.001], bins=10, label='y_last!=0', alpha=0.5)
plt.title('Relative valid error')
plt.legend(loc='best')
#plt.show()

#print predict value for 66th week
subplot(2,2,4)
values = non_nan_res['Error_valid'].values
plt.hist(values[y_last<=0.001], bins=10, label='y_last=0', alpha=0.5)
plt.hist(values[y_last>0.001], bins=10, label='y_last!=0', alpha=0.5)
plt.title('Error_valid')
plt.legend(loc='best')
#plt.show()

# <codecell>

from sklearn.metrics import roc_curve, auc

y_true = (y_last>0.001)*1
#y_score = non_nan_res[str(param3)].values
y_score = non_nan_res['Error_valid'].values/(non_nan_res[str(param3)].values+2.0)
fpr, tpr, _ = roc_curve(y_true, y_score, pos_label=None, sample_weight=None)
roc_auc = auc(fpr, tpr)

figure(figsize=(15, 5))
subplot(1,2,1)
plt.plot(fpr, tpr)
plt.title('ROC curve')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
print 'ROC AUC is ', roc_auc

# <codecell>

def GetCoord(xedges, yedges, x, y):
    for i in range(0,len(xedges)):
        if x<xedges[i]:
            break
            
    for j in range(0,len(yedges)):
        if y<yedges[j]:
            break
    
    return i-1,j-1

# <codecell>

from matplotlib.colors import LogNorm

figure(figsize=(20, 10))

subplot(231)
plt.hist2d(y_last, non_nan_res[str(param3)].values, norm=LogNorm(), bins=20)
plt.colorbar()
plt.xlabel('Value of the last point in test')
plt.ylabel('Predicted value of the last point in test')
plt.title('LogNormed histogram for test')

subplot(232)
(counts, xedges, yedges, Image) = plt.hist2d(y_valid_last, non_nan_res[str(param3-t)].values, norm=LogNorm(), bins=20)
plt.colorbar()
plt.xlabel('Value of the last point in valid')
plt.ylabel('Predicted value of the last point in valid')
plt.title('LogNormed histogram for valid')

counts_std = counts/counts.max()
y_score = []
for i in range(0, len(y_last)):
    x,y = GetCoord(xedges, yedges, y_valid_last[i], non_nan_res[str(param3-t)].values[i])
    y_score.append(1-counts_std[x,y])
y_score = np.array(y_score)

subplot(2,3,3)
plt.hist(y_score[y_last<=0.001], label='y_true=0', alpha=0.5)
plt.hist(y_score[y_last>0.001], label = 'y_true!=0', alpha=0.5)
plt.legend(loc='best')
plt.title("y_score distribution")

subplot(234)
plt.hist2d(y_last, y_score, norm=LogNorm(), bins=20)
plt.xlabel('Value of the last point in test')
plt.ylabel('y_score')
plt.title('LogNormed histogram for test')
plt.colorbar()

subplot(235)
plt.hist2d(y_valid_last, y_score, norm=LogNorm(), bins=20)
plt.xlabel('Value of the last point in valid')
plt.ylabel('y_score')
plt.title('LogNormed histogram for valid')
plt.colorbar()

from sklearn.metrics import roc_curve, auc

y_true = (y_last>0.001)*1
fpr, tpr, _ = roc_curve(y_true, y_score, pos_label=None, sample_weight=None)
roc_auc = auc(fpr, tpr)

subplot(2,3,6)
plt.plot(fpr, tpr, label='ROC auc = '+str(roc_auc))
plt.title('ROC curve')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.legend(loc='best')

# <codecell>

avg_value_predict_test = []
avg_value_true_test = []
avg_value_predict_valid = []
avg_value_true_valid = []
test_cols = [i for i in range(param3-t,param3)]
valid_cols = [i for i in range(param3-t-v,param3-t)]

for row in range(0,non_nan_res.shape[0]):
    avg_val_pred_test = non_nan_res[test_cols].irow([row]).mean(axis=1).values[0]
    avg_value_predict_test.append(avg_val_pred_test)
    avg_val_true_test = df_ts_rolling_sum_std[range(105-t,105)].irow([row]).mean(axis=1).values[0]
    avg_value_true_test.append(avg_val_true_test)
    
    avg_val_pred_valid = non_nan_res[valid_cols].irow([row]).mean(axis=1).values[0]
    avg_value_predict_valid.append(avg_val_pred_valid)
    avg_val_true_valid = df_ts_rolling_sum_std[range(105-t-v,105-t)].irow([row]).mean(axis=1).values[0]
    avg_value_true_valid.append(avg_val_true_valid)
    
avg_value_predict_test = np.array(avg_value_predict_test)
avg_value_true_test = np.array(avg_value_true_test)
avg_value_predict_valid = np.array(avg_value_predict_valid)
avg_value_true_valid = np.array(avg_value_true_valid)

# <codecell>

figure(figsize=(15, 10))

subplot(2,2,1)
values = avg_value_predict_test
plt.hist(values[avg_value_true_test<=0.001], bins=20, label='avg_value_true=0', alpha=0.5)
plt.hist(values[avg_value_true_test>0.001], bins=20, label='avg_value_true!=0', alpha=0.5)
plt.title('Predict values')
plt.legend(loc='best')

subplot(2,2,2)
values = avg_value_predict_valid - avg_value_true_valid
plt.hist(values[avg_value_true_test<=0.001], bins=20, label='avg_value_true=0', alpha=0.5)
plt.hist(values[avg_value_true_test>0.001], bins=20, label='avg_value_true!=0', alpha=0.5)
plt.title('Error valid')
plt.legend(loc='best')

subplot(2,2,3)
values = (avg_value_predict_valid - avg_value_true_valid)/(avg_value_predict_test+2.0)
plt.hist(values[avg_value_true_test<=0.001], bins=20, label='avg_value_true=0', alpha=0.5)
plt.hist(values[avg_value_true_test>0.001], bins=20, label='avg_value_true!=0', alpha=0.5)
plt.title('Relative valid error')
plt.legend(loc='best')

subplot(2,2,4)
values = avg_value_predict_valid - avg_value_true_valid
plt.hist(values[avg_value_true_test<=0.001], bins=20, label='avg_value_true=0', alpha=0.5)
plt.hist(values[avg_value_true_test>0.001], bins=20, label='avg_value_true!=0', alpha=0.5)
plt.title('Error_valid')
plt.legend(loc='best')

# <codecell>

from sklearn.metrics import roc_curve, auc

y_true_avg = (avg_value_true_test>0.001)*1
y_score_avg = 0.3*(avg_value_predict_test+1.0)
#y_score_avg = 0.5*(avg_value_predict_valid - avg_value_true_valid)/(avg_value_predict_test+2.0)+0.5
fpr_avg, tpr_avg, _ = roc_curve(y_true_avg, y_score_avg, pos_label=None, sample_weight=None)
roc_auc_avg = auc(fpr_avg, tpr_avg)

figure(figsize=(15, 5))
subplot(1,2,1)
plt.plot(fpr_avg, tpr_avg)
plt.title('ROC curve')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
print 'ROC AUC is ', roc_auc_avg

# <codecell>

figure(figsize=(20, 10))

subplot(231)
plt.hist2d(avg_value_true_test, avg_value_predict_test, norm=LogNorm(), bins=20)
plt.colorbar()
plt.xlabel('Value of the last point in test')
plt.ylabel('Predicted value of the last point in test')
plt.title('LogNormed histogram for test')

subplot(232)
(counts, xedges, yedges, Image) = plt.hist2d(avg_value_true_valid, avg_value_predict_valid, norm=LogNorm(), bins=20)
plt.colorbar()
plt.xlabel('Value of the last point in valid')
plt.ylabel('Predicted value of the last point in valid')
plt.title('LogNormed histogram for valid')

counts_std = counts/counts.max()
y_score = []
for i in range(0, len(y_last)):
    x,y = GetCoord(xedges, yedges, avg_value_true_valid[i], avg_value_predict_valid[i])
    y_score.append(1-counts_std[x,y])
y_score = np.array(y_score)

subplot(2,3,3)
plt.hist(y_score[avg_value_true_test<=0.001], label='y_true=0', alpha=0.5)
plt.hist(y_score[avg_value_true_test>0.001], label = 'y_true!=0', alpha=0.5)
plt.legend(loc='best')
plt.title("y_score distribution")

subplot(234)
plt.hist2d(avg_value_true_test, y_score, norm=LogNorm(), bins=20)
plt.xlabel('Value of the last point in test')
plt.ylabel('y_score')
plt.title('LogNormed histogram for test')
plt.colorbar()

subplot(235)
plt.hist2d(avg_value_true_valid, y_score, norm=LogNorm(), bins=20)
plt.xlabel('Value of the last point in valid')
plt.ylabel('y_score')
plt.title('LogNormed histogram for valid')
plt.colorbar()

from sklearn.metrics import roc_curve, auc

y_true = (avg_value_true_test>0.001)*1
fpr, tpr, _ = roc_curve(y_true, y_score, pos_label=None, sample_weight=None)
roc_auc = auc(fpr, tpr)

subplot(2,3,6)
plt.plot(fpr, tpr, label='ROC auc = '+str(roc_auc))
plt.title('ROC curve')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.legend(loc='best')

# <codecell>

val_cols = [i for i in range(1,105-param1+1)] 
non_nan_res = results[(pd.isnull(results).sum(axis=1)==0)*(results['Error_valid']<=2)*(results['Error_train']<=2)*\
                      (results['inter_max']<=20)]
#non_nan_res[val_cols] = (non_nan_res[val_cols].values>=0.95)*1
non_nan_res.shape

# <codecell>

max_values = df_ts_rolling_sum.max(axis=1)
df_ts_rolling_sum_std = df_ts_rolling_sum.copy()
for col in df_ts_rolling_sum.columns:
    df_ts_rolling_sum_std[col] = df_ts_rolling_sum[col]/max_values

# <codecell>

val_cols = [i for i in range(1,105-param1+1)]
val_x = range(param1,105)
cols = range(param1,105)
a=0
b=60
N=b-a
figure(figsize=(15, 5*(N//3+1)))
for row in range(a,b):
    subplot(N//3+1,3,row)
    plt.plot(val_x,non_nan_res[val_cols].irow([row]).values[0], color='r', label='predict')
    index = int(non_nan_res.irow([row])['Index'].values)
    plt.plot(cols, df_ts_rolling_sum_std[cols].xs(index), color='b', label='real')
    plt.plot([105-t,105-t], [-1,1], color='black')
    plt.plot([105-v-t,105-v-t], [-1,1], color='black')
    plt.title('Index is '+str(index))
    #plt.xlim(ws,105)
    plt.ylim(-1,1.1)
    plt.legend(loc='best')
    #plt.show()

# <codecell>

#print error hists
figure(figsize=(15, 5))
subplot(121)
plt.hist(non_nan_res['Error_test'].values, color='r', bins=20, label='test', alpha=1, histtype='step')
plt.hist(non_nan_res['Error_train'].values, color='b', bins=20, label='train', alpha=1, histtype='step')
plt.hist(non_nan_res['Error_valid'].values, color='g', bins=20, label='valid', alpha=1, histtype='step')
plt.title('Errors')
plt.legend(loc='best')
#plt.show()

#print predict value for the last point
subplot(122)
plt.hist(non_nan_res[str(param3)].values, bins=10, label='last point')
plt.title('Predict values')
plt.legend(loc='best')
#plt.show()

# <codecell>

y_last=[]
y_valid_last = []
for i in non_nan_res['Index']:
    i=int(i)
    cur_serie = df_ts_rolling_sum.xs(i).values
    y_last.append(cur_serie[param3-10]/(1.0*cur_serie.max()))
    y_valid_last.append(cur_serie[param3-v-t]/(1.0*cur_serie.max()))
y_last = np.array(y_last)
y_valid_last = np.array(y_valid_last)

# <codecell>

non_nan_res[y_last<=0.001].shape

# <codecell>

figure(figsize=(15, 10))
#print predict value for the last point
subplot(2,2,1)
values = non_nan_res[str(param3)].values
plt.hist(values[y_last<=0.001], bins=10, label='y_last=0', alpha=0.5)
plt.hist(values[y_last>0.001], bins=10, label='y_last!=0', alpha=0.5)
plt.title('Predict values')
plt.legend(loc='best')
#plt.show()

#print predict value for 66th week
subplot(2,2,2)
values = non_nan_res['Error_test'].values
plt.hist(values[y_last<=0.001], bins=10, label='y_last=0', alpha=0.5)
plt.hist(values[y_last>0.001], bins=10, label='y_last!=0', alpha=0.5)
plt.title('Error_test')
plt.legend(loc='best')
#plt.show()

#print predict value for 66th week
subplot(2,2,3)
values = non_nan_res['Error_valid'].values/(non_nan_res[str(param3)].values+2.0)
plt.hist(values[y_last<=0.001], bins=10, label='y_last=0', alpha=0.5)
plt.hist(values[y_last>0.001], bins=10, label='y_last!=0', alpha=0.5)
plt.title('Relative valid error')
plt.legend(loc='best')
#plt.show()

#print predict value for 66th week
subplot(2,2,4)
values = non_nan_res['Error_valid'].values
plt.hist(values[y_last<=0.001], bins=10, label='y_last=0', alpha=0.5)
plt.hist(values[y_last>0.001], bins=10, label='y_last!=0', alpha=0.5)
plt.title('Error_valid')
plt.legend(loc='best')
#plt.show()

# <codecell>

from sklearn.metrics import roc_curve, auc

y_true = (y_last>0.001)*1
y_score = non_nan_res[str(param3)].values
#y_score = non_nan_res['Error_valid'].values/(non_nan_res[str(param3)].values+2.0)
fpr, tpr, _ = roc_curve(y_true, y_score, pos_label=None, sample_weight=None)
roc_auc = auc(fpr, tpr)

figure(figsize=(15, 5))
subplot(1,2,1)
plt.plot(fpr, tpr)
plt.title('ROC curve')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
print 'ROC AUC is ', roc_auc

# <codecell>

def GetCoord(xedges, yedges, x, y):
    for i in range(0,len(xedges)):
        if x<xedges[i]:
            break
            
    for j in range(0,len(yedges)):
        if y<yedges[j]:
            break
    
    return i-1,j-1

# <codecell>

from matplotlib.colors import LogNorm

figure(figsize=(20, 10))

subplot(231)
plt.hist2d(y_last, non_nan_res[str(param3)].values, norm=LogNorm(), bins=20)
plt.colorbar()
plt.xlabel('Value of the last point in test')
plt.ylabel('Predicted value of the last point in test')
plt.title('LogNormed histogram for test')

subplot(232)
(counts, xedges, yedges, Image) = plt.hist2d(y_valid_last, non_nan_res[str(param3-t)].values, norm=LogNorm(), bins=20)
plt.colorbar()
plt.xlabel('Value of the last point in valid')
plt.ylabel('Predicted value of the last point in valid')
plt.title('LogNormed histogram for valid')

counts_std = counts/counts.max()
y_score = []
for i in range(0, len(y_last)):
    x,y = GetCoord(xedges, yedges, y_valid_last[i], non_nan_res[str(param3-t)].values[i])
    y_score.append(1-counts_std[x,y])
y_score = np.array(y_score)

subplot(2,3,3)
plt.hist(y_score[y_last<=0.001], label='y_true=0', alpha=0.5)
plt.hist(y_score[y_last>0.001], label = 'y_true!=0', alpha=0.5)
plt.legend(loc='best')
plt.title("y_score distribution")

subplot(234)
plt.hist2d(y_last, y_score, norm=LogNorm(), bins=20)
plt.xlabel('Value of the last point in test')
plt.ylabel('y_score')
plt.title('LogNormed histogram for test')
plt.colorbar()

subplot(235)
plt.hist2d(y_valid_last, y_score, norm=LogNorm(), bins=20)
plt.xlabel('Value of the last point in valid')
plt.ylabel('y_score')
plt.title('LogNormed histogram for valid')
plt.colorbar()

from sklearn.metrics import roc_curve, auc

y_true = (y_last>0.001)*1
fpr, tpr, _ = roc_curve(y_true, y_score, pos_label=None, sample_weight=None)
roc_auc = auc(fpr, tpr)

subplot(2,3,6)
plt.plot(fpr, tpr, label='ROC auc = '+str(roc_auc))
plt.title('ROC curve')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.legend(loc='best')

# <codecell>

avg_value_predict_test = []
avg_value_true_test = []
avg_value_predict_valid = []
avg_value_true_valid = []
test_cols = [i for i in range(param3-t,param3)]
valid_cols = [i for i in range(param3-t-v,param3-t)]

for row in range(0,non_nan_res.shape[0]):
    avg_val_pred_test = non_nan_res[test_cols].irow([row]).mean(axis=1).values[0]
    avg_value_predict_test.append(avg_val_pred_test)
    avg_val_true_test = df_ts_rolling_sum_std[range(105-t,105)].irow([row]).mean(axis=1).values[0]
    avg_value_true_test.append(avg_val_true_test)
    
    avg_val_pred_valid = non_nan_res[valid_cols].irow([row]).mean(axis=1).values[0]
    avg_value_predict_valid.append(avg_val_pred_valid)
    avg_val_true_valid = df_ts_rolling_sum_std[range(105-t-v,105-t)].irow([row]).mean(axis=1).values[0]
    avg_value_true_valid.append(avg_val_true_valid)
    
avg_value_predict_test = np.array(avg_value_predict_test)
avg_value_true_test = np.array(avg_value_true_test)
avg_value_predict_valid = np.array(avg_value_predict_valid)
avg_value_true_valid = np.array(avg_value_true_valid)

# <codecell>

figure(figsize=(15, 10))

subplot(2,2,1)
values = avg_value_predict_test
plt.hist(values[avg_value_true_test<=0.001], bins=20, label='avg_value_true=0', alpha=0.5)
plt.hist(values[avg_value_true_test>0.001], bins=20, label='avg_value_true!=0', alpha=0.5)
plt.title('Predict values')
plt.legend(loc='best')

subplot(2,2,2)
values = avg_value_predict_valid - avg_value_true_valid
plt.hist(values[avg_value_true_test<=0.001], bins=20, label='avg_value_true=0', alpha=0.5)
plt.hist(values[avg_value_true_test>0.001], bins=20, label='avg_value_true!=0', alpha=0.5)
plt.title('Error valid')
plt.legend(loc='best')

subplot(2,2,3)
values = (avg_value_predict_valid - avg_value_true_valid)/(avg_value_predict_test+2.0)
plt.hist(values[avg_value_true_test<=0.001], bins=20, label='avg_value_true=0', alpha=0.5)
plt.hist(values[avg_value_true_test>0.001], bins=20, label='avg_value_true!=0', alpha=0.5)
plt.title('Relative valid error')
plt.legend(loc='best')

subplot(2,2,4)
values = avg_value_predict_valid - avg_value_true_valid
plt.hist(values[avg_value_true_test<=0.001], bins=20, label='avg_value_true=0', alpha=0.5)
plt.hist(values[avg_value_true_test>0.001], bins=20, label='avg_value_true!=0', alpha=0.5)
plt.title('Error_valid')
plt.legend(loc='best')

# <codecell>

from sklearn.metrics import roc_curve, auc

y_true_avg = (avg_value_true_test>0.001)*1
#y_score_avg = 0.5*(avg_value_predict_test+2.0)
y_score_avg = 0.5*(avg_value_predict_valid - avg_value_true_valid)/(avg_value_predict_test+2.0)+0.5
fpr_avg, tpr_avg, _ = roc_curve(y_true_avg, y_score_avg, pos_label=None, sample_weight=None)
roc_auc_avg = auc(fpr_avg, tpr_avg)

figure(figsize=(15, 5))
subplot(1,2,1)
plt.plot(fpr_avg, tpr_avg)
plt.title('ROC curve')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
print 'ROC AUC is ', roc_auc_avg

# <codecell>

figure(figsize=(20, 10))

subplot(231)
plt.hist2d(avg_value_true_test, avg_value_predict_test, norm=LogNorm(), bins=20)
plt.colorbar()
plt.xlabel('Value of the last point in test')
plt.ylabel('Predicted value of the last point in test')
plt.title('LogNormed histogram for test')

subplot(232)
(counts, xedges, yedges, Image) = plt.hist2d(avg_value_true_valid, avg_value_predict_valid, norm=LogNorm(), bins=20)
plt.colorbar()
plt.xlabel('Value of the last point in valid')
plt.ylabel('Predicted value of the last point in valid')
plt.title('LogNormed histogram for valid')

counts_std = counts/counts.max()
y_score = []
for i in range(0, len(y_last)):
    x,y = GetCoord(xedges, yedges, avg_value_true_valid[i], avg_value_predict_valid[i])
    y_score.append(1-counts_std[x,y])
y_score = np.array(y_score)

subplot(2,3,3)
plt.hist(y_score[avg_value_true_test<=0.001], label='y_true=0', alpha=0.5)
plt.hist(y_score[avg_value_true_test>0.001], label = 'y_true!=0', alpha=0.5)
plt.legend(loc='best')
plt.title("y_score distribution")

subplot(234)
plt.hist2d(avg_value_true_test, y_score, norm=LogNorm(), bins=20)
plt.xlabel('Value of the last point in test')
plt.ylabel('y_score')
plt.title('LogNormed histogram for test')
plt.colorbar()

subplot(235)
plt.hist2d(avg_value_true_valid, y_score, norm=LogNorm(), bins=20)
plt.xlabel('Value of the last point in valid')
plt.ylabel('y_score')
plt.title('LogNormed histogram for valid')
plt.colorbar()

from sklearn.metrics import roc_curve, auc

y_true = (avg_value_true_test>0.001)*1
fpr, tpr, _ = roc_curve(y_true, y_score, pos_label=None, sample_weight=None)
roc_auc = auc(fpr, tpr)

subplot(2,3,6)
plt.plot(fpr, tpr, label='ROC auc = '+str(roc_auc))
plt.title('ROC curve')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.legend(loc='best')

# <codecell>

import ipykee
#ipykee.create_project(project_name="D._UsageForecast", repository="git@github.com:hushchyn-mikhail/CERN_Time_Series.git")
session = ipykee.Session(project_name="D._UsageForecast")

