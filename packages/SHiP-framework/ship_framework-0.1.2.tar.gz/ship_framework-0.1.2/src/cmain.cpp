#include <cnpy.h>

#include <framework/SHiP.hpp>
#include <framework/partitioning/available_partitionings.hpp>
#include <framework/tree_construction/available_trees.hpp>
#include <framework/tree_construction/tree_construction.hpp>
#include <framework/tree_construction/ultrametric_tree_structure.hpp>
#include <framework/print_functions.hpp>
#include <iostream>
#include <memory>
#include <vector>


using namespace std;



std::vector<std::vector<double>> pointer_to_vector(double* data, long long n, long long dim) {
    std::vector<std::vector<double>> vdata(n, std::vector<double>(dim));
    // Fill the inner vectors with data
    for (long long i = 0; i < n; ++i) {
        std::copy(data + i * dim, data + (i + 1) * dim, vdata[i].begin());
    }
    return vdata;
}



int main(int argc, char* argv[]) {
    cout << "Load: " << argv[1] << endl;
    // Load the .npy file
    cnpy::NpyArray arr = cnpy::npy_load(argv[1]);

    double* array = arr.data<double>();

    std::vector<std::vector<double>> vdata = pointer_to_vector(array, arr.shape[0], arr.shape[1]);
    cout << vdata.size() << " " << vdata[0].size() << endl;


    for (auto type : get_available_ultrametric_tree_types_as_strings()) {
        cout << type << ", ";
    }
    cout << endl;



    // UltrametricTree tree = constructUltrametricTree(vdata, string_to_ultrametric_tree_type(argv[2]));

    // // Serialize to JSON
    // std::string json = tree.root->toJson();
    // // std::cout << "Serialized JSON:\n"
    // //           << json << "\n";

    // // Deserialize back to object
    // simdjson::dom::parser parser;
    // simdjson::dom::element root_element = parser.parse(json);

    // auto root = std::make_shared<UltrametricTreeNode>(0, 0.0);
    // if (root->fromJson(root_element)) {
    //     std::cout << "Parsed successfully!\n";
    // } else {
    //     std::cerr << "Failed to parse.\n";
    // }
    // std::cout << "Deserialized Root ID: " << root->id << ", Cost: " << root->cost << "\n";

    // // Optional: simple print to verify
    // std::cout << "Root ID: " << root->id << "\n";
    // for (const auto& child : root->children) {
    //     std::cout << " Child ID: " << child->id << ", Cost: " << child->cost << "\n";
    //     for (const auto& grandchild : child->children) {
    //         std::cout << "  Grandchild ID: " << grandchild->id << ", Cost: " << grandchild->cost << "\n";
    //     }
    // }


    auto ship = SHiP(vdata, string_to_ultrametric_tree_type(argv[2]), 0, string_to_partitioning_method(argv[3]));
    auto res = ship.fit_predict();
    cout << res.size() << endl;

    res = ship.fit_predict(2);
    cout << res.size() << endl;

    std::string json = ship.get_tree()->to_json(true);

    // cout << endl << json << endl << endl;

    auto root = std::make_shared<UltrametricTreeNode>(0, 0.0);
    UltrametricTree tree(root, UltrametricTreeType::LoadTree);
    cout << (tree.from_json(json) ? "Success" : "Failure") << endl;

    cout << ultrametric_tree_type_to_string(tree.tree_type) << endl;

    // printTree(tree.root);

    return 0;
}
