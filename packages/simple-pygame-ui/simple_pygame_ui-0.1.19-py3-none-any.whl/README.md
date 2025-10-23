# PyGameUI Is a PyGame UI Library that adds simple UI for with the use of PyGame

## Setting up a simple setup:

in your Main Class write:

```python
if __name__ == "__main__":
  pygameui.setup(YourMainScene())
```

and also make a Script and add a class to that script in my Case "YourMainScene"

```python
class YourMainScene(PyGameScene):
  def update(self):
    # Write your Code here that Should only run when the Window is updated
  def render(self,screen,events):
    # Write your Rendering Code here
```
now lets say you want to add a Button then write a snippet like this in update:

```python
self.drawables.append(Button("Here Goes the Button Text",
  (Here Goes a tuple of 2 ints that is the center of the button),
  (Here Goes a tuple of 2 ints that is the size of the button),
  heres a reference for what should happen when the button gets clicked(lamda supported),
  [Heres a list of values that should be passed onto the on_clicked methode]))
```
