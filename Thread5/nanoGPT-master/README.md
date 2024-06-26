## Here is how you can run this experiment

### The path of experiment

All the code should be run under ``DeepDelight\Thread5\nanoGPT-master`` folder, you should go to this folder before run the experiment.

### Data preparation

Before you run this code, make sure you have the input data prepared. There are two dataset for this experiment. TinyShakespeare and Pride and Prejudice. You should select which dataset you want to use for this experiment. The default data set is TinyShakespeare. To change the input data, you should modify code in ``DeepDelight\Thread5\nanoGPT-master\data\shakespeare_char\prepare.py`` You should first delete existing ``input.txt`` and run the ``prepare.py``.

### Explaination of each script

Once you have your data prepared, you can run the script to start the expriment. For configs, you can change all the config files under ``DeepDelight\Thread5\nanoGPT-master\config`` folder. Different ending have different meaning, the attention dropout rate is set and you can change iterations and layers by change the config files.

- For ``test1.sh``, it is a experiment about attention connection dropout. You can simply run ``test1.sh`` and it will run automaticlly. Also, the visualization code will also run automaticlly.
- For ``test2.sh``, it is a experiment about one layer residual connection dropout. You can simply run ``test2.sh`` and it will run automaticlly. Also, the visualization code will also run automaticlly.
- For ``test3.sh``, it is a experiment about two layer residual connection dropout. You can simply run ``test3.sh`` and it will run automaticlly. Also, the visualization code will also run automaticlly.

### Structure of code

The are 5 main part code in this expriment.

1. Configs: ``configs.py`` store all the configs to the model. In this part, you can define iteration times and n_layer etc.
2. Model: ``model.py`` defines the model. It contains the structure of the model so if you want to change the nerual network structure, you should modify this code.
3. Test script: ``test.sh`` is bash script file that allows you to run serveral command easily. Also it record the training time and save it in ``train_time.txt``.
4. Train: ``train.py`` contains feed forward function and record all the train loss and val loss.
5. Visualization: ``visualizaion.py`` utilize train loss and val loss generated by ``train.py`` to generate visualization. 

### Example to run a experiment

1. Run ``DeepDelight\Thread5\nanoGPT-master\data\shakespeare_char\prepare.py``
2. Run ``test.sh``

By default, it will run 5000 iteration on TinyShakespeare dataset.
