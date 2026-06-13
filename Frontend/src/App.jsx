import React, { useState, useEffect } from "react";
import { generate, API } from "./api";
import { MapContainer, TileLayer, CircleMarker } from "react-leaflet";

export default function App() {

  const parameterConfig = {
    stitchlength: {
      label: "Stitch Length (mm)",
      type: "number",
      min: 0,
      step: 0.1
    },
    stitchheight: {
      label: "Stitch Height (mm)",
      type: "number",
      min: 0,
      step: 0.1
    },
    stitchsetback: {
      label: "Stitch Setback (mm)",
      type: "number",
      min: 0,
      step: 0.1
    },
    diametercm: {
      label: "Globe Diameter (cm)",
      type: "number",
      min: 0,
      step: 0.1
    },
    amountofteststitches: {
      label: "Amount of Test Stitches",
      type: "number",
      min: 0,
      step: 1
    },
    lengthoftestyarn: {
      label: "Length of Test Yarn",
      type: "number",
      min: 0,
      step: 0.1
    },
    kind: {
      label: "Part of the globe",
      type: "select",
      options: [
        { value: "globe", label: "Whole globe" },
        { value: "south", label: "Southern hemisphere" },
        { value: "north", label: "Northern hemisphere" }
      ]
    }
  };

  function ParameterInput({ name, value, config, onChange }) {
    const { label, type } = config;

    return (
      <label className="flex flex-col text-sm font-medium">
        {label}:

        {type === "number" && (
          <input
            type="number"
            min={config.min}
            step={config.step}
            value={value}
            onChange={e => onChange(name, Number(e.target.value))}
            className="mt-1 border rounded px-2 py-1 text-sm focus:outline-none focus:ring focus:ring-blue-300"
          />
        )}

        {type === "select" && (
          <select
            value={value}
            onChange={e => onChange(name, e.target.value)}
            className="mt-1 border rounded px-2 py-1 text-sm focus:outline-none focus:ring focus:ring-blue-300"
          >
            {config.options.map(opt => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        )}
      </label>
    );
  }

  const [params, setParams] = useState({
    stitchlength: 2,
    stitchheight: 2,
    stitchsetback: 1,
    diametercm: 1,
    amountofteststitches: 100,
    lengthoftestyarn: 3,
    kind: "globe"
  });

  const updateParam = (key, value) => {
    setParams(prev => ({ ...prev, [key]: value }));
  };

  const paramLabels = {
    stitchlength: "Stitch Length (mm)",
    stitchheight: "Stitch Height (mm)",
    stitchsetback: "Stitch Setback (mm)",
    diametercm: "Globe Diameter (cm)",
    amountofteststitches: "Amount of Test Stitches",
    lengthoftestyarn: "Length of Test Yarn",
    kind: "Part of the globe"
  };

  const [markers, setMarkers] = useState([]);
  const [index, setIndex] = useState(0);
  const [stats, setStats] = useState(null);

  function formatMarker(marker) {
    return marker.map(entry => {
      const [count, _mal, inc, c1, c2] = entry;

      if (inc === 0) return `${count} × sc ${c1}`;
      if (inc === 1) {
        if (!c2 || c2 === c1) return `${count} × inc ${c1}`;
        return `${count} × inc  (${c1} + ${c2})`;
      }
      if (inc === -1) return `${count} × dec ${c1}`;

      return `${count} × ??? (${c1}${c2 ? " + " + c2 : ""})`;
    });
  }

  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === "ArrowRight") {
        setIndex(i => Math.min(i + 1, markers.length - 1));
      }
      if (e.key === "ArrowLeft") {
        setIndex(i => Math.max(i - 1, 0));
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [markers]);

  async function run() {
    const result = await generate(params);
    setMarkers(result.pattern);
    setIndex(0);
    setStats(result.statistics);
  }

  const current = markers[index];

  function prev() {
    setIndex(i => Math.max(0, i - 1));
  }

  function next() {
    setIndex(i => Math.min(markers.length - 1, i + 1));
  }

  return (
    <div className="p-20 relative min-h-screen bg-gray-50">

      <h1 className="text-5xl font-bold mb-6 text-center">
        🌍Crochet Pattern Generator: Globe🌍
      </h1>

      <div className="flex flex-col md:flex-row md:items-start gap-6 pt-15"> {/*oberer abschnitt*/}

        {/* Parameter Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-1/2 pr-10">
          {Object.entries(parameterConfig).map(([key, config]) => (
            <ParameterInput
              key={key}
              name={key}
              value={params[key]}
              config={config}
              onChange={updateParam}
            />
          ))}
        </div>

        {/* Instructions box */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800 p-7 rounded w-1/2">
          <h3 className="font-semibold mb-2">Instruction</h3>
          <p>
        
<ol>
    <li>
        Crochet a small test circle, for example starting with 6 single crochet stitches (sc) and increasing by 6 stitches in each round.
    </li>
    <li>
        Measure the dimensions of a single stitch:
        <ul>
            <li>Stitch width (mm)</li>
            <li>Stitch height (mm)</li>
        </ul>
    </li>
    <li>
        Measure the stitch offset:
        <ul>
            <li>Observe how the stitches shift from one round to the next.</li>
            <li>Measure the resulting offset per round in millimeters.</li>
        </ul>
    </li>
    <li>
        Determine yarn consumption:
        <ul>
            <li>Count the total number of stitches in the test piece.</li>
            <li>Unravel the circle.</li>
            <li>Measure the length of yarn used in centimeters.</li>
        </ul>
    </li>
    <li>
        Choose your preferred globe construction method:
        <ul>
            <li>Crochet the entire globe as a single piece and stuff it immediately.</li>
            <li>Crochet the northern and southern hemispheres separately and join them at the equator.</li>
        </ul>
    </li>
    <li>
        If you are making a pillow cover, you can connect both hemispheres with a zipper instead of sewing them together permanently.
    </li>
    <li>
        Enter all measured values into the form and click <strong>"GENERATE"</strong>.
    </li>
    <li>
        The application will automatically generate:
        <ul>
            <li>The crochet pattern</li>
            <li>The estimated yarn requirements for each color</li>
        </ul>
    </li>
    <li>
        Abbreviations:
        <ul>
            <li><strong>sc</strong> = single crochet</li>
            <li><strong>inc</strong> = increase</li>
            <li><strong>dec</strong> = decrease</li>
        </ul>
    </li>
</ol>

            At first crochet a small test circle, eg. start with 6 sc and increase
            6 in each row. Then measure the height and width of each stitch in mm.
            Furthermore, you will notice that the stiches do not sit exactly on
            top of each other. Measure the setback that occurs in each row in mm.
            Count the amount of stitches, unravel and measure the length of the
            yarn you needed in cm.
            Also, there are two ways of crocheting the globe. Either the whole globe at once and stuff it immideately,
            or the northern and southern hemisphere separately and sew them together at the equator. In my case, the
            globe will be a cover for a pillow, so I will connect them with a zipper. Enter the data and klick "GENERATE". The pattern
            and the amount of yarn you need of each color will appear. Here "sc"
            means single crochet, "inc" means increase and "dec" means decrease.
          </p>
        </div>

      </div>

        <div className="flex justify-center items-center mt-5 ">
      <div className="flex justify-center mt-5 w-1/2">
        <button
          onClick={run}
          className="px-10 py-6 bg-red-900 text-white rounded hover:bg-red-400 transition-colors"
        >
          GENERATE
        </button>
      </div>



      {markers.length === 0 ? (
        <p className="text-gray-600 mt-2 text-center w-1/2">No Data.</p>
      ) : (
        <div className="mt-4 flex flex-col items-center gap-4 w-1/2">
          <h2 className="text-2xl font-semibold mt-8 text-center">Pattern</h2>
          <div className="flex items-center gap-4 w-full max-w-xxl">

            <button
              onClick={prev}
              disabled={index === 0}
              className="px-3 py-2 bg-gray-200 rounded disabled:opacity-40 hover:bg-gray-300 transition-colors"
            >
              ←
            </button>

            <pre className="bg-white p-4 rounded max-h-72 overflow-auto whitespace-pre-wrap flex-grow shadow">
              {formatMarker(current).map((line, i) => {
                let color = "black";
                if (line.includes("blue")) color = "#4778ba";
                if (line.includes("yellow")) color = "#f6aa48";
                if (line.includes("green")) color = "#476e3d";
                if (line.includes("sand")) color = "#c99d75";
                if (line.includes("olive")) color = "#615c49";
                if (line.includes("gray")) color = "#6e6d75";

                return (
                  <div key={i} style={{ color }}>
                    {line}
                  </div>
                );
              })}
            </pre>

            <button
              onClick={next}
              disabled={index === markers.length - 1}
              className="px-3 py-2 bg-gray-200 rounded disabled:opacity-40 hover:bg-gray-300 transition-colors"
            >
              →
            </button>

          </div>

          <p className="mt-3 text-gray-700">
            Element {index + 1} von {markers.length}
          </p>

        </div>
      )}
</div>
      <div className="pt-20">
      <table className="w-full text-sm mt-8">
        <thead>
          <tr>
            <th className="text-left border-b pb-1">Color</th>
            <th className="text-right border-b pb-1">Stitches</th>
            <th className="text-right border-b pb-1">Length (cm)</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(stats || {}).map(([color, { count, length }]) => (
            <tr key={color}>
              <td className="py-1">{color}</td>
              <td className="py-1 text-right">{count}</td>
              <td className="py-1 text-right">{length}</td>
            </tr>
          ))}
        </tbody>
      </table>
  </div>
    </div>
  );
}
