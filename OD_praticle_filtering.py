import numpy as np
import scipy.stats
from numpy.random import randn, random
import matplotlib.pyplot as plt

def create_uniform_particles(x_range, N):
    particles = np.random.rand(N)*x_range
    return particles

def predict(particles, u, std, dt=1.):
    N = len(particles)
    particles += u*dt + (randn(N) * std)

def update(particles, weights, z, R, landmarks):
    weights.fill(1.)
    for i, landmark in enumerate(landmarks):
        distance = abs(particles-landmark)
        weights *= scipy.stats.norm(distance, R).pdf(z[i])

    weights += 1.e-300  # avoid round-off to zero
    weights /= sum(weights)  # normalize


def estimate(particles, weights):
    pos = particles
    mean = np.average(pos, weights=weights, axis=0)
    var = np.average((pos - mean) ** 2, weights=weights, axis=0)
    return mean, var


def neff(weights):
    return 1. / np.sum(np.square(weights))


def simple_resample(particles, weights):
    N = len(particles)
    cumulative_sum = np.cumsum(weights)
    cumulative_sum[-1] = 1.  # avoid round-off error
    indexes = np.searchsorted(cumulative_sum, random(N))

    # resample according to indexes
    particles[:] = particles[indexes]
    weights[:] = weights[indexes]
    weights /= np.sum(weights)  # normalize


def run_pf(N, iters=18, sensor_std_err=0.1):
    landmarks = np.array([20])
    NL = len(landmarks)

    # create particles and weights
    particles = create_uniform_particles(20, N)
    weights = np.zeros(N)
    robot_pos = np.array(0.)
    xs = []
    for x in range(iters):
        robot_pos += 1

        # distance from robot to each landmark
        zs = (landmarks - robot_pos)

        # move particles forward to (x+1, x+1)
        predict(particles, u=1.414, std=0.2)
        update(particles, weights, z=zs, R=sensor_std_err, landmarks=landmarks)

        if neff(weights) < N / 2:
           simple_resample(particles, weights)

        mu, var = estimate(particles, weights)
        xs.append(mu)
    gs = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18
                   ])
    ys = np.array([15])
    xs = np.array(xs)
    plt.plot(np.arange(iters + 1), 'k+')
    plt.plot(xs[:], gs, 'r.')
    plt.scatter(landmarks[:], ys, alpha=0.4, marker='o',  s=100)  # plot landmarks
    plt.legend(['Actual', 'PF'], loc=4, numpoints=1)
    plt.xlim([-2, 22])
    plt.ylim([0, 22])
    print('estimated position and variance:\n\t', mu, var)
    plt.show()


if __name__ == '__main__':
    run_pf(N=5000)
