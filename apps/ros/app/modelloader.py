from JumpScale import j
import os

def find_models(basepath):
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
                specs[namespace] = models
            fullspecs[type_] = specs
    return fullspecs
