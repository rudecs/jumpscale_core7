## better support for toml

* create tools in jumpscale to deal with toml
* check if the python implementation has all feature we require
* see if we can improve the toml serializer to get some of the features we put in hrd

### toml min required features

* comments
* multi line strings support

### improvements to serializer

* try to get a certain order of serialization this allows better change management using tools like git
* try to always serialize in the same way
    * e.g. when array bigger than certain size than multiline
    * e.g. when string bigger than certain size multiline
* goal is to serialize in such a way that its as human friendly readable as possible

### specs toml

* https://github.com/toml-lang/toml

### remarks

* in a next project we want to optimize the golang serializer to have same features as the python one, this to make sure that serialized .toml files look alike as much as possible

### where will this be used

* allow @ys to also use .toml in stead of .hrd
    * this will allow in future an @ys implementation in golang
* serialization/deserialization in our new osis (this to version control data behind an osis in a more automated way)


