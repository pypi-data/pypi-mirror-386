Example
=======

.. code-block:: python

   from SHiP import SHiP

   ship = SHiP(data=data, treeType="DCTree")

   # or to load a saved tree
   ship = SHiP(data=data, treeType="LoadTree", config={"json_tree_filepath": "<file_path>"}) 
   # or additionally specify the tree_type of the loaded tree by adding {"tree_type": "DCTree"}

   ship.hierarchy = 0
   ship.partitioningMethod = "K"
   labels = ship.fit_predict()

   # or in one line
   labels = ship.fit_predict(hierarchy = 1, partitioningMethod = "Elbow")

   # optional: save the current computed tree
   json = ship.get_tree().to_json()
