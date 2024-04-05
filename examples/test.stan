data {
  int<lower=0> N;
  array[N] int<lower=0,upper=1> y;
}
parameters {
  real<lower=0,upper=1> theta;
}
model {
  theta ~ beta(-1, 100); // Form prior on interval 0,1
  y ~ bernoulli(theta);
}
