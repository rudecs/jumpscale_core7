from JumpScale import j
import os
import importlib

def find_model_specs(basepath):
    modelbasepath = os.path.join(basepath, 'models', 'osis')
    fullspecs = dict()
    for type_ in ('mongo', 'sql'):
        modelpath = os.path.join(modelbasepath, type_)
        specs = dict()
        if os.path.exists(modelpath):
            for namespace in j.system.fs.listDirsInDir(modelpath, dirNameOnly=True):
                specpath = os.path.join(modelpath, namespace)
                j.core.specparser.parseSpecs(specpath, 'osismodel', namespace)
                modelnames = j.core.specparser.getModelNames('osismodel', namespace)
                models = dict()
                for modelname in modelnames:
                    model = j.core.specparser.getModelSpec('osismodel', namespace, modelname)
                    models[modelname] = model
                if models:
                    specs[namespace] = models
            if specs:
                fullspecs[type_] = specs
    return fullspecs

def find_model_files(basepath):
    modelbasepath = os.path.join(basepath, 'models', 'osis')
    modelpath = os.path.join(modelbasepath, 'sql')
    if os.path.exists(modelpath):
        result = {} 
        for namespace in j.system.fs.listDirsInDir(modelpath, dirNameOnly=True):
            namspacepath =  os.path.join(modelpath, namespace)
            modules = [path for path in os.listdir(namspacepath) if path.endswith('.py')]
            for module in modules:
                result[namespace] = result.get(namespace, [])
                result[namespace].append(module.replace('.py', ''))
    return result