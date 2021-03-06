# -*- coding: utf-8 -*-
"""Libr for sat.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1bMkIPPYnmr55KZqBlhRA_Tia08smUSjP
"""

import numpy as np
import matplotlib.pyplot as plt

from scipy.stats import norm
from scipy.optimize import root

from keras.models import Sequential
from keras.optimizer_v2.adam import Adam
from keras.optimizer_v2.gradient_descent import SGD
from keras.layers.core import Dense, Flatten
from keras.layers import BatchNormalization
from keras.initializers import initializers_v1



def make_test(proba_F, num_neuro, edu_size):


  def P_F(q_0):                       
    return 1 - norm.cdf(q_0)             #вычисление вероятности ложной  тревоги

  def P_D(q_0, q):

    return 1 - norm.cdf(q_0 - np.sqrt(2*q))       #вычисление вероятности правильного обнаружения

  def fun(d_q):
    return P_F(d_q) - F


  def find_q_0():
    return root(fun, np.array([0]), method = 'hybr')



  def correlator(realization, signal_s, delta_t):
    return delta_t * realization.dot(signal_s)



  def edu_vyborka_gen(num_s, num_n, sigma, t, signal_s):
    edu_s = []
    target_s = []
    edu_n = []
    target_n = []

    for i in range(num_s):

      #генерация реализаций с сигналом
      noise = sigma * np.random.randn(len(t))
      realization = signal_s + noise
      edu_s.append(realization)
      target_s.append(1)

    for i in range(num_n):
      #генерация реализаций без сигнала (только шум)
      noise = sigma * np.random.randn(len(t))
      realization = noise
      edu_n.append(realization)
      target_n.append(0)

    edu_s = np.asarray(edu_s)
    edu_n = np.asarray(edu_n)

    target_s = np.asarray(target_s)
    target_n = np.asarray(target_n)

    edu = np.concatenate((edu_s, edu_n), axis = 0)
    targets = np.concatenate((target_s, target_n), axis = 0)

    return edu, targets




  def test_vyborka_gen(sigma, num_all, t, signal_s):
    test_s = []
    test_n = []


    for i in range(num_all):

      #генерация реализациий с сигналом

      noise = sigma * np.random.randn(len(t))
      realization = signal_s + noise
      test_s.append(realization)


      #генерация реализаций только с шумом, без сигнала

      noise = sigma * np.random.randn(len(t))
      realization = noise
      test_n.append(realization)


    test_s = np.asarray(test_s)
    test_n = np.asarray(test_n)

    return test_s, test_n
  #параметры простого радиоимпульса, который нужно обнаружить


  f_pch = 30*(10**3)
  T = 1*(10**(-3))
  phi_0 = 0

  f_d = 1/T
  T_d = 1/f_d

  f_d_1 = 20*f_pch
  T_d_1 = 1/f_d_1        #две частоты дискретизации, первая - после РЧБ, до обнаружителя

  sigma_n = 1  #СКО АБГШ

  #из СКО перейдем к спектральной плотности мощности АБГШ

  N_0 = 2*sigma_n*sigma_n/f_d_1


  rq = 3.2

  E = rq*rq*N_0

  A = np.sqrt(2*E/T)   #находим амплитуду сигнала


  num = np.fix(T/T_d_1)
  num = np.int(num)

  t = np.linspace(0, T, num)

  print('A =', A)

  signal = A*np.cos(2 * np.pi * f_pch * t + phi_0)     #модель сигнала



  #найдем количество выборок сигнала и шума

  F = proba_F       #требуемая вероятность ложной тревоги

  q_0 = find_q_0().x[0]    #важно перейти к соотношению априорных вероятностей

  z_0 = q_0*rq*np.sqrt(2)


  h = np.exp(z_0 - rq*rq)

  print(h)

  #edu_num = 100000 #варьируемый параметр - это количество реализациий, которые будцт переданы для обучения
  edu_num = edu_size

  num_signal = int(edu_num/(1+h))      #количество реализаций с сигналом в обучающей выборке
  num_noise = edu_num - num_signal     #количество реализаций с шумом в обучабщей выборке


  edu_data_no, targets = edu_vyborka_gen(num_signal, num_noise, sigma_n, t, signal)

  targets = targets.reshape(len(targets), 1)


  #создаем модель искуственной нейросети, используя фраемворк Keras

  inputs = len(edu_data_no[0])
  #hidden = 50
  hidden = num_neuro
  l_rate = 0.0001
  num_epochs = 100

  model = Sequential()
  #model.add(Flatten())
  model.add(BatchNormalization())
  model.add(Dense(hidden, input_shape = (inputs, ), activation = 'tanh'))
  model.add(Dense(1, activation = 'sigmoid'))

  model.compile(loss = 'binary_crossentropy', optimizer = Adam(learning_rate = l_rate),
                metrics = ['AUC'])

  #обучаем созданную модель искуственной нейронной сети

  model.fit(edu_data_no, targets, epochs = num_epochs, verbose = 2, shuffle = True)


  #сохранить обученную модель
  model_json = model.to_json()
  with open("/content/drive/My Drive/Files_of_detecting/model_i.json", "w") as json_file:
      json_file.write(model_json)
  # serialize weights to HDF5
  model.save_weights("/content/drive/My Drive/Files_of_detecting/model_i.h5")
  print("Saved model to disk")



  root_q = np.arange(0, 4.2, 0.05)

  optimal_P_D = []
  corr_P_D = []
  corr_P_F = []
  neuro_P_D = []
  neuro_P_F = []

  for r_q in root_q:

    E = r_q*r_q*N_0

    A = np.sqrt(2*E/T)   #находим амплитуду сигнала


    num = np.fix(T/T_d_1)
    num = np.int(num)

    t = np.linspace(0, T, num)

    print('A =', A)

    signal = A*np.cos(2 * np.pi * f_pch * t + phi_0)     #модель сигнала



    #найдем количество выборок сигнала и шума

    F = 0.001       #требуемая вероятность ложной тревоги

    q_0 = find_q_0().x[0]    #важно перейти к соотношению априорных вероятностей

    z_0 = q_0*r_q*np.sqrt(2)


    h = np.exp(z_0 - r_q*r_q)

    print(h)

    edu_num = 100000 #варьируемый параметр - это количество реализациий, которые будцт переданы для обучения

    num_signal = int(edu_num/(1+h))      #количество реализаций с сигналом в обучающей выборке
    num_noise = edu_num - num_signal     #количество реализаций с шумом в обучабщей выборке

    test_num = 10000                     #количетсво реализаций в тестовой выборке

    #генерируем обучающую выборку


    #edu_data_no, targets = edu_vyborka_gen(num_signal, num_noise, sigma_n, t, signal)

    #targets = targets.reshape(len(targets), 1)
    #scaler = MinMaxScaler()

    #edu_data = scaler.fit_transform(edu_data_no)

    #генерируем тестовую выборку

    tests_signal, tests_noise = test_vyborka_gen(sigma_n, test_num, t, signal)

    P_D_theory = P_D(q_0, r_q*r_q)

    optimal_P_D.append(P_D_theory)


    y_pred_signals = model.predict(tests_signal)
    y_pred_noise = model.predict(tests_noise)



    P_D_est = 0
    P_F_est = 0

    P_D_est_nn = 0
    P_F_est_nn = 0 

    for i in range(len(tests_signal)):

      #сигнал есть в реализации, считаем оценку вероятности правильного обнаружения

      E = root_q[-2]*root_q[-2]*N_0

      A = np.sqrt(2*E/T)   #находим амплитуду сигнала


      num = np.fix(T/T_d_1)
      num = np.int(num)



      signal = A*np.cos(2 * np.pi * f_pch * t + phi_0)     #модель сигнала

      corr_res = (2/N_0)*correlator(tests_signal[i], signal, T_d_1)

      z_0 = q_0*root_q[-2]*np.sqrt(2)

      if corr_res >= z_0:
        P_D_est = P_D_est + 1
      #print(corr_res)

      #сигнала нет в реализации, считаем вероятность ложной тревоги

      corr_res_n = (2/N_0)*correlator(tests_noise[i], signal, T_d_1)

      if corr_res_n >= z_0:
        P_F_est = P_F_est + 1



      if y_pred_signals[i] >= 0.5:
        P_D_est_nn = P_D_est_nn + 1

      if y_pred_noise[i] >= 0.5:
        P_F_est_nn = P_F_est_nn + 1


    P_D_est = P_D_est/len(tests_signal)
    P_F_est = P_F_est/len(tests_noise)

    P_D_est_nn = P_D_est_nn/len(tests_signal)
    P_F_est_nn = P_F_est_nn/len(tests_noise)

    corr_P_D.append(P_D_est)
    corr_P_F.append(P_F_est)

    neuro_P_D.append(P_D_est_nn)
    neuro_P_F.append(P_F_est_nn)

    #сбор вероятностей

  corr_P_D = np.asarray(corr_P_D)
  optimal_P_D = np.asarray(optimal_P_D)
  neuro_P_D = np.asarray(neuro_P_D)

  metric_us_d = []
  metric_us_f = []
  for p_d_nn, p_d_opt in zip(neuro_P_D, optimal_P_D):
    if p_d_nn >= 0.95*p_d_opt:
      metric_us_d.append(1)
    else:
      metric_us_d.append(0)

  for p_f_nn in neuro_P_F:
    if p_f_nn <= 0.003:
      metric_us_f.append(1)
    else:
      metric_us_f.append(0)

  metric_us_d = np.asarray(metric_us_d)
  metric_us_f = np.asarray(metric_us_f)

  metric_us_d = np.sum(metric_us_d)
  metric_us_f = np.sum(metric_us_f)

  metric_us_d = metric_us_d/(len(root_q) - 1)
  metric_us_f = metric_us_f/len(root_q)

  return metric_us_d, metric_us_f
