import importlib.metadata

__version__ = importlib.metadata.version("mofresh") 

import io 
import base64
import anywidget
import matplotlib
import matplotlib.pylab as plt 
import traitlets
from tempfile import TemporaryDirectory
from pathlib import Path


matplotlib.use('Agg')


class ImageRefreshWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      let src = () => model.get("src");
      let image = document.createElement("img");
      image.src = src();
      model.on("change:src", () => {
        image.src = src();
      });
      el.appendChild(image);
    }
    export default { render };
    """
    src = traitlets.Unicode().tag(sync=True)


def altair2svg(chart):
    # Need to write to disk to get SVG, filetype determines how to store it
    # have not found an api in altair that can return a variable in memory
    with TemporaryDirectory() as tmp_dir:
        chart.save(Path(tmp_dir) / "example.svg")
        return (Path(tmp_dir) / "example.svg").read_text()


class HTMLRefreshWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      let elem = () => model.get("html");
      let div = document.createElement("div");
      div.innerHTML = elem();
      model.on("change:html", () => {
        div.innerHTML = elem();
      });
      el.appendChild(div);
    }
    export default { render };
    """
    html = traitlets.Unicode().tag(sync=True)


def refresh_matplotlib(func):
    def wrapper(*args, **kwargs):
        # Reset the figure to prevent accumulation. Maybe we need a setting for this?
        fig = plt.figure()

        # Run function as normal
        func(*args, **kwargs)

        # Store it as base64 and put it into an image.
        my_stringIObytes = io.BytesIO()
        plt.savefig(my_stringIObytes, format='jpg')
        my_stringIObytes.seek(0)
        my_base64_jpgData = base64.b64encode(my_stringIObytes.read()).decode()

        # Close the figure to prevent memory leaks
        plt.close(fig)
        plt.close('all')
        return f'data:image/jpg;base64, {my_base64_jpgData}'
    return wrapper


def refresh_altair(func):
    def wrapper(*args, **kwargs):
        # Run function as normal
        altair_chart = func(*args, **kwargs)
        return altair2svg(altair_chart)
    return wrapper


class ProgressBar(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
        let getValue = () => model.get("value");
        let getMaxValue = () => model.get("max_value");

        const container = document.createElement('div');
        container.style.width = '100%';
        container.style.marginBottom = '10px';
        container.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';

        // Label
        const label = document.createElement('div');
        label.style.marginBottom = '8px';
        label.style.fontSize = '13px';
        label.style.fontWeight = '500';
        label.style.color = '#666';

        // Progress bar container
        const barContainer = document.createElement('div');
        barContainer.style.width = '100%';
        barContainer.style.height = '24px';
        barContainer.style.borderRadius = '12px';
        barContainer.style.overflow = 'hidden';
        barContainer.style.backgroundColor = '#e0e0e0';
        barContainer.style.border = '1px solid #ccc';
        barContainer.style.boxShadow = 'inset 0 1px 3px rgba(0,0,0,0.1)';

        // Progress fill
        const fill = document.createElement('div');
        fill.style.height = '100%';
        fill.style.transition = 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
        fill.style.display = 'flex';
        fill.style.alignItems = 'center';
        fill.style.justifyContent = 'center';
        fill.style.background = 'linear-gradient(90deg, #888 0%, #777 100%)';
        fill.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';

        // Percentage text
        const text = document.createElement('span');
        text.style.fontSize = '11px';
        text.style.fontWeight = '600';
        text.style.color = 'white';
        text.style.textShadow = '0 1px 2px rgba(0,0,0,0.3)';
        text.style.letterSpacing = '0.5px';

        const updateDisplay = () => {
            const value = getValue();
            const max = getMaxValue();
            const percentage = max > 0 ? (value / max) * 100 : 0;

            label.textContent = `Progress: ${value} / ${max}`;
            fill.style.width = percentage + '%';
            text.textContent = Math.round(percentage) + '%';

            // Update text visibility based on bar width
            text.style.opacity = percentage > 10 ? '1' : '0';
        };

        fill.appendChild(text);
        barContainer.appendChild(fill);
        container.appendChild(label);
        container.appendChild(barContainer);

        updateDisplay();

        model.on('change:value', updateDisplay);
        model.on('change:max_value', updateDisplay);

        el.appendChild(container);
    }

    export default { render };
    """

    value = traitlets.Int(0).tag(sync=True)
    max_value = traitlets.Int(100).tag(sync=True)
