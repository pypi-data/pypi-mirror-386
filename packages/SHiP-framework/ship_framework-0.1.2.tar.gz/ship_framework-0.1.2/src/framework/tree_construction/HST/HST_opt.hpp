/**
    \Author: Trasier
    \Date:    2019/06/18
**/

#pragma once

#include <string>

#include "global.hpp"


extern const long long MAX_SAMPLE;
extern const long long MAX_HEIGHT;
extern long long H;
extern long long alpha;
extern double* expks;
extern double* sumks;
extern long long* pi;
extern long long* reverse_pi;
extern double dmax;
extern double beta;


struct Node_t {
    long long nid;      // the idx of the node
    long long nomIdx;   // the id of norminator point
    long long lev;      // the level of the node before compression
    Node_t* far;  // the parent node
    long long cid;      // the position of this node in its parent's child list.
    double wei;    // the weight of the edge from its parent
    std::vector<Node_t*> child;
    double dist;
    long long pid = -1;

    Node_t(long long nid_ = 0, long long nomIdx_ = 0, long long lev_ = 0, Node_t* far_ = NULL, double wei_ = 0) {
        nid = nid_;
        nomIdx = nomIdx_;
        lev = lev_;
        far = far_;
        wei = wei_;
        cid = 0;
        dist = 0;
    }
};

extern Node_t* rt;
extern Node_t** leaves;

void mergeChild(Node_t* far, Node_t* u);
void addChild(Node_t* far, Node_t* u);
void initLocation(std::string& fileName);
void initMemory_HST(std::vector<std::vector<double>>& data);
void freeMemory_HST();
void freeHST(Node_t*& rt);
void constructHST_fast_dp(std::vector<std::vector<double>>& data, long long seed = -1);
void constructHST_fast_opt(std::vector<std::vector<double>>& data);
void randomization(long long seed = -1);
void calcDmaxPrune();
double distAtLevel(long long level);
double distOnHST(long long u, long long v);
double distOnHST(Node_t* u, Node_t* v);
std::pair<Node_t*, long long> getLCA(long long u, long long v);
std::pair<Node_t*, long long> getLCA(Node_t* u, Node_t* v);
long long levelOfLCA(long long u, long long v);
long long levelOfLCA(Node_t* u, Node_t* v);
double calcDists(Node_t* rt);
