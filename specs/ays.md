# AtYourService - @YS

## Goals
### Deployment system :
- easy installation
- full live cycle monitoring of an application
    + build
    + install
    + reset
    + start
    + stop
    + restart
    + monitor
    + import data
    + export data
- possibility to install on **remote machines.**

### Modeling system :
#### concepts :
@ys can be used to models an full environment, from the more general  (location, data-center) to the most specific (port-forward on a switch) component.

The modeling if done trough **2 files** :
- An **HRD file** that contains the metadata and describe the service/component 
- a **python file** that contains the business logic of every action possible for the service/component.
- A service is identified by it's domain, name, instance and parent
- all files are located inside a directory names ```domain__name__instance```
    example : for a mongo service we could have ```jumpscale__mongodb__main```

#### Environment management :
The modeling and management of a environment will used the remote installation feature.  
The idea is that we have all services that models the environment inside a git repo on a 'master' machine. This machine is used to manage the all environment and git is used to have version of the model.

Just a look at the services on the 'master' machine will give us a full view of the status of the environment. Then it's vital to keep the local services synced with the actual instance of them remotely

#### Relations between services
##### Parent/childs
- A service is the parent of other services.
- All child services are located inside the directory of the parent.
```
parent
 |
 | - child1
     | action.py
     | service.hrd
 | - child2
     | action.py
     | service.hrd
 | action.py
 | service.hrd
```
- A service is also identified by it's parent, so two services with the same domain/name/instance can exits if they have different parents.

##### Producer/Consumer
@ys package can provide a service, it's called a producer.
To use these producer, one needs a consumer, so @ys package can also be a consumer.

A service can be producer and consumer at the same time. this allows chaining of services that work all together.

Two producer of the same type, can be replace one by another seamlessly.
(?? need to define an interface for a type of producer ??)

## Implementation
### Deployment system :

####  Local deployment
- **Build** :
    - look into HRD for source file location and compiler needed to compile.
    - compile the service
    - upload binary to binary repo
- **Installation**:
    Just follow recipe from HRD file to get data and dependencies, then execute code from actions.py file.
- **Reset**:
    + reset remove all trace from a service
    + need to remove service directory and installed files.
    + ?? dependencies management ?? go over dependencies, check if other services require this dependency, if yes keep, if not, remove too.

#### Remote deployment
- **Build** :
    - No supported for remote machines
- **Installation**:
    - Need a service that describe the machine where to deploy. Any producer service of **type node** is valid.
    - Initialize all dependencies locally.
        + Retrieve the dependency chain of the service we install.
        + Fill HRD files for all dependencies, but don't download anything on the local machine.
    - send service and dependencies to remote machine.
    - remote machine loads all services in memory and install them locally.
- **Reset** :
    + send command to remote to reset the service.
    + if no error, reset the service locally too
- **Start/Stop** :
    + If we try to start/stop a service, means it's installed already, so we just send the start/stop command to the remote node.