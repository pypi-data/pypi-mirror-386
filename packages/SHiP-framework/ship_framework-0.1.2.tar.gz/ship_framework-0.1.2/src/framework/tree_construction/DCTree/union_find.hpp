#include <vector>

class UnionFind {
private:
    std::vector<unsigned long long> parent;  // Parent array
    std::vector<unsigned long long> rank;    // Rank array

public:
    // Constructor
    UnionFind(unsigned long long n) {
        parent.resize(n);
        for (unsigned long long i = 0; i < n; ++i) {
            parent[i] = i;  // Each node is its own parent initially
        }
        rank.resize(n, 1);  // Initialize rank to 1
    }

    // Find function with path compression
    unsigned long long find(unsigned long long x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);  // Path compression
        }
        return parent[x];
    }

    // Union function to unite the sets containing x and y
    unsigned long long union_set(unsigned long long x, unsigned long long y) {
        unsigned long long xset = find(x);
        unsigned long long yset = find(y);
        if (xset == yset) {
            return xset;  // Already in the same set
        }

        // Union by rank
        if (rank[xset] < rank[yset]) {
            parent[xset] = yset;
            return yset;
        } else if (rank[xset] > rank[yset]) {
            parent[yset] = xset;
            return xset;
        } else {
            parent[yset] = xset;  // Move y under x
            rank[xset] += 1;      // Increment the rank of x's tree
            return xset;
        }
    }
};