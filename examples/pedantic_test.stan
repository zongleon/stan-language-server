data {
  int N;
  array[N] real x;
}
parameters {
  real sigma;
}
model {
  real mu;
  x ~ normal(mu, sigma);
}
