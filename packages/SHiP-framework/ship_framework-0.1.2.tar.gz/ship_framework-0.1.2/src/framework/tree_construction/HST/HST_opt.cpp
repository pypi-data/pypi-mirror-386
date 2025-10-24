/**
    \Author: Trasier
    \Date:    2019/06/18
**/

#include "HST_opt.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <random>

#include "global.hpp"


const long long MAX_HEIGHT = 40;
long long H = 0;
long long alpha = 2;
double logAlpha = 1.0;
long long* pi = NULL;
long long* reverse_pi = NULL;
double dmax = -1.0;
double* expks = NULL;
double* sumks = NULL;
Node_t* rt = NULL;
Node_t** leaves = NULL;
double beta = 1.0;

inline double custom_log2(double x) {
    return std::log(x) / logAlpha;
}

inline double pow2(long long i) {
    return (i < 0) ? 1.0 : expks[i];
}

inline long long getLevel(long long H, double dist) {
    if (dist < 1.0) return H + 1;

    long long k = (long long)std::ceil(custom_log2(dist / beta));

    if (expks[k] * beta == dist)
        ++k;

    return H + 1 - k;
}

void initMemory_HST(std::vector<std::vector<double>>& data) {
    nV = data.size();
    V = data;
    squaredScaleFactor = 1.0;

    double scaleFactor = 1.0;
    for (long long i = 0; i < nV; ++i) {
        for (long long j = 0; j < nV; ++j) {
            double d = dist(V, i, j);
            if (d > 0) {
                scaleFactor = std::min(d, scaleFactor);
            }
        }
    }
    squaredScaleFactor = scaleFactor * scaleFactor;

    pi = new long long[nV];
    reverse_pi = new long long[nV];
    expks = new double[MAX_HEIGHT + 1];
    expks[0] = 1.0;
    for (long long i = 1; i <= MAX_HEIGHT; ++i)
        expks[i] = expks[i - 1] * (double)alpha;

    sumks = new double[MAX_HEIGHT + 1];
    sumks[0] = expks[0];
    for (long long i = 1; i <= MAX_HEIGHT; ++i)
        sumks[i] = sumks[i - 1] + expks[i];

    leaves = new Node_t*[nV];

    logAlpha = log(alpha);
}

void freeMemory_HST() {
    delete[] pi;
    delete[] reverse_pi;
    delete[] expks;
    delete[] sumks;
    delete[] leaves;
    freeHST(rt);
}

void freeHST(Node_t*& rt) {
    if (rt == NULL) return;

    Node_t* chi;

    for (unsigned long long i = 0; i < rt->child.size(); ++i) {
        chi = rt->child[i];
        freeHST(chi);
    }

    delete rt;
    rt = NULL;
}


void randomization(long long seed) {
    // set seed
    std::mt19937 rng;
    if (seed != -1) {
        rng = std::mt19937(seed);
    } else {
        rng = std::mt19937(time(0));
    }

    // generate the permutation pi
    for (long long i = 0; i < nV; ++i) {
        pi[i] = i;
    }
    std::shuffle(pi, pi + nV, rng);
    for (long long i = 0; i < nV; ++i) {
        reverse_pi[pi[i]] = i;
    }
    // generate the parameter gamma
    beta = (double)(rand() % alpha + 1) * 1.0 / (double)alpha;
}

inline void addChild(Node_t* far, Node_t* u) {
    u->far = far;
    u->cid = far->child.size();
    far->child.push_back(u);
}

static long long merge_n;

inline void mergeChild(Node_t* far, Node_t* u) {
    if (far == rt || far->child.size() != 1)
        return;

    Node_t* gfar = far->far;
    long long gcid = far->cid;

    u->far = far->far;
    u->cid = gcid;
    u->wei += far->wei;

    gfar->child[gcid] = u;
    delete far;
    merge_n++;
}

void constructHST_fast_opt(std::vector<std::vector<double>>& data) {
    initMemory_HST(data);

    // label the far[][] with node ID
    long long nid = 1;
    long long *cnt = NULL, *cen = NULL;
    Node_t** nodes = NULL;
    Node_t** nodes_ = NULL;
    double* cenl = NULL;
    long long *p = NULL, *q = NULL, *far = NULL, *far_ = NULL;

    // cnt[i]: count
    // p: x
    // q:
    cnt = new long long[nV];
    cen = new long long[nV];
    cenl = new double[nV];
    p = new long long[nV];
    q = new long long[nV];
    far = new long long[nV];
    far_ = new long long[nV];
    nodes = new Node_t*[nV];
    nodes_ = new Node_t*[nV];

    if (rt != NULL)
        freeHST(rt);
    randomization();

    // Prunning 1: calcDmax()
    dmax = 0;
    for (long long i = 0; i < nV; ++i) {
        cen[i] = 0;
        cenl[i] = dist(V, i, pi[cen[i]]);
        dmax = std::max(dmax, cenl[i]);
    }

    // initialization
    H = (long long)ceil(custom_log2(dmax + EPS)) + 1;
    double radius = pow2(H) * beta;

    // construct the root
    rt = new Node_t(0, pi[0], 1, NULL, radius);
    for (long long i = 0; i < nV; ++i) {
        nodes_[i] = rt;
        far[i] = far_[i] = 0;
        p[i] = i;
    }

    merge_n = 0;
    for (long long k = 2; k <= H + 1; ++k) {
        radius /= (double)alpha;
        for (long long i = 0; i < nV; ++i) {
            if (cenl[i] < radius)
                continue;

            long long pid;
            while (cenl[i] >= radius) {
                pid = pi[++cen[i]];
                if (cen[pid] <= reverse_pi[i]) {
                    cenl[i] = dist(V, i, pi[cen[i]]);
                }
            }
        }

        long long bid = nid, i = 0, bi;
        memset(q, -1, sizeof(long long) * nV);
        while (i < nV) {
            q[cen[p[i]]] = far[p[i]] = nid++;
            bi = i++;
            while (i < nV && far_[p[i]] == far_[p[i - 1]]) {
                long long pid = cen[p[i]];
                if (q[pid] == -1) {
                    q[pid] = nid++;
                }
                far[p[i]] = q[pid];
                ++i;
            }
            while (bi < i) {
                long long pid = cen[p[bi]];
                q[pid] = -1;
                ++bi;
            }
        }
        memset(cnt, 0, sizeof(long long) * nV);
        for (long long i = 0; i < nV; ++i) {
            ++cnt[far[i] - bid];
        }
        for (long long j = 1; j < nid - bid; ++j) {
            cnt[j] += cnt[j - 1];
        }
        for (long long i = nV - 1; i >= 0; --i) {
            long long j = far[p[i]] - bid;
            q[--cnt[j]] = p[i];
        }
        // create the new node at the $k$-th level
        for (long long i = 0, j = 0; i < nV; i = j) {
            j = i;
            nodes[q[i]] = new Node_t(far[q[i]], pi[cen[q[i]]], k, nodes_[q[i]], radius);
            addChild(nodes_[q[i]], nodes[q[i]]);
            while (j < nV && far[q[j]] == far[q[i]]) {
                nodes[q[j]] = nodes[q[i]];
                ++j;
            }
        }
        // merge the new node with its parent
        for (long long i = 0, j = 0; i < nV; i = j) {
            j = i;
            mergeChild(nodes_[q[i]], nodes[q[i]]);
            while (j < nV && far[q[j]] == far[q[i]]) {
                ++j;
            }
        }
        // fill in the leaves
        if (k == H + 1) {
            for (long long i = 0; i < nV; ++i) {
                leaves[q[i]] = nodes[q[i]];
            }
        }
        std::swap(far, far_);
        std::swap(p, q);
        std::swap(nodes, nodes_);
    }

    usedMemory = 0;
    usedMemory += (nid - merge_n) * sizeof(Node_t);
    usedMemory += nV * 2 * sizeof(long long);

    delete[] cnt;
    delete[] cen;
    delete[] cenl;
    delete[] p;
    delete[] q;
    delete[] far;
    delete[] far_;
    delete[] nodes;
    delete[] nodes_;
}

double distAtLevel(long long lev) {
    if (lev >= H + 1) return 0.0;
    return sumks[H - lev] * beta * 2.0;
}

double distOnHST(long long u, long long v) {
    long long level = levelOfLCA(u, v);
    return distAtLevel(level);
}

double distOnHST(Node_t* u, Node_t* v) {
    long long level = levelOfLCA(u, v);
    return distAtLevel(level);
}

long long levelOfLCA(long long u, long long v) {
    return levelOfLCA(leaves[u], leaves[v]);
}

long long levelOfLCA(Node_t* u, Node_t* v) {
    if (u == NULL || v == NULL)
        return -1;

    while (u != NULL && v != NULL && u->lev != v->lev) {
        if (u->lev > v->lev) {
            u = u->far;
        } else {
            v = v->far;
        }
    }

    if (u == NULL || v == NULL)
        return -1;

    return u->lev;
}

std::pair<Node_t*, long long> getLCA(long long u, long long v) {
    return getLCA(leaves[u], leaves[v]);
}

std::pair<Node_t*, long long> getLCA(Node_t* u, Node_t* v) {
    if (u == NULL || v == NULL)
        return std::make_pair(rt, -1);

    while (u != NULL && v != NULL && u != v) {
        if (u->lev > v->lev) {
            u = u->far;
        } else {
            v = v->far;
        }
    }

    if (u == NULL || v == NULL)
        return std::make_pair(rt, -1);

    return std::make_pair(u, u->lev);
}

void calcDmaxPrune() {
    dmax = 0;
    for (long long j = 1; j < nV; ++j) {
        dmax = std::max(dmax, dist(V, pi[0], j));
    }
}

void constructHST_fast_dp(std::vector<std::vector<double>>& data, long long seed) {
    initMemory_HST(data);
    // perm[i][j]: center of node i at level j
    // reverse LEVEL in the tree as

    randomization(seed);
    calcDmaxPrune();

    // initialization
    H = (long long)ceil(custom_log2(dmax + EPS)) + 1;
    double radius = pow2(H) * beta;
    long long** perm = new long long*[nV];
    for (long long i = 0; i < nV; ++i) {
        perm[i] = new long long[H + 2];
    }

    // using DP to construct the HST
    for (long long i = 0; i < nV; i++) {
        perm[i][1] = 0;
        for (long long j = 2; j <= H + 1; ++j) {
            perm[i][j] = reverse_pi[i];
        }
        for (long long j = 0; j < reverse_pi[i]; j++) {
            double curd = dist(V, i, pi[j]);
            long long k = getLevel(H, curd);
            perm[i][k] = std::min(perm[i][k], j);
        }

        perm[i][H + 1] = reverse_pi[i];
        for (long long k = H; k >= 1; --k) {
            perm[i][k] = std::min(perm[i][k], perm[i][k + 1]);
        }
    }

    // label the far[][] with node ID
    long long nid = 1;
    long long *cnt = NULL, *p = NULL, *q = NULL;
    long long *far = NULL, *far_ = NULL;
    Node_t** nodes = NULL;
    Node_t** nodes_ = NULL;

    // cnt[i]: count
    // p: x
    // q: result
    cnt = new long long[nV];
    far = new long long[nV];
    far_ = new long long[nV];
    p = new long long[nV];
    q = new long long[nV];
    nodes = new Node_t*[nV];
    nodes_ = new Node_t*[nV];

    // construct the root
    rt = new Node_t(0, pi[0], 1, NULL, 0);
    for (long long i = 0; i < nV; ++i) {
        nodes_[i] = rt;
        p[i] = i;
        far_[i] = 0;
    }

    for (long long k = 2; k <= H + 1; ++k) {
        radius /= (double)alpha;
        long long bid = nid, i = 0, bi;
        memset(q, -1, sizeof(long long) * nV);
        while (i < nV) {
            q[perm[p[i]][k]] = far[p[i]] = nid++;
            bi = i++;
            while (i < nV && far_[p[i]] == far_[p[i - 1]]) {
                long long pid = perm[p[i]][k];
                if (q[pid] == -1) {
                    q[pid] = nid++;
                }
                far[p[i]] = q[pid];
                ++i;
            }
            while (bi < i) {
                long long pid = perm[p[bi]][k];
                q[pid] = -1;
                ++bi;
            }
        }
        memset(cnt, 0, sizeof(long long) * nV);
        for (long long i = 0; i < nV; ++i) {
            ++cnt[far[i] - bid];
        }
        for (long long j = 1; j < nid - bid; ++j) {
            cnt[j] += cnt[j - 1];
        }
        for (long long i = nV - 1; i >= 0; --i) {
            long long j = far[p[i]] - bid;
            q[--cnt[j]] = p[i];
        }
        // create the new node at the $k$-th level
        for (long long i = 0, j = 0; i < nV; i = j) {
            j = i;
            nodes[q[i]] = new Node_t(far[q[i]], pi[perm[q[i]][k]], k, nodes_[q[i]], radius);
            addChild(nodes_[q[i]], nodes[q[i]]);
            while (j < nV && far[q[j]] == far[q[i]]) {
                nodes[q[j]] = nodes[q[i]];
                ++j;
            }
        }
        // merge the new node with its parent
        for (long long i = 0, j = 0; i < nV; i = j) {
            j = i;
            mergeChild(nodes_[q[i]], nodes[q[i]]);
            while (j < nV && far[q[j]] == far[q[i]]) {
                ++j;
            }
        }
        if (k == H + 1) {
            for (long long j = 0; j < nV; ++j) {
                leaves[j] = nodes[j];
                leaves[j]->pid = j;
            }
        }
        std::swap(q, p);
        std::swap(far, far_);
        std::swap(nodes, nodes_);
    }

    usedMemory = 0;
    usedMemory += nid * sizeof(Node_t);
    usedMemory += nV * (H + 2) * sizeof(long long);

    delete[] cnt;
    delete[] far;
    delete[] far_;
    delete[] p;
    delete[] q;
    delete[] nodes;
    delete[] nodes_;
    for (long long i = 0; i < nV; ++i)
        delete[] perm[i];
    delete[] perm;
}

double calcDists(Node_t* node) {
    if (node->child.empty()) {
        return node->wei;
    }
    double dist;
    for (Node_t* child : node->child) {
        dist = calcDists(child);
    }
    node->dist = 2 * dist;
    return node->wei + dist;
}
