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
      
      {/* Instructions box */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800 p-7 rounded w-1/1">
          <h3 className="font-semibold mb-2">Instruction</h3>

        

      <div id="rp8pr0">
    <p><strong>Step 1:</strong></p>
    <ul>
        <li>Crochet a small test circle, for example starting with 6 sc and increasing by 6 stitches in each round. Measure the width and the height of a single stitch (mm). Observe how the stitches shift from one round to the next. Measure also the resulting offset per round (mm).</li>
    </ul>

    <p><strong>Step 2 (Optional):</strong></p>
    <ul>
        <li>To obtain an estimate on the expected yarn consumption, count the total number of stitches and unravel the test piece. Measure the length of yarn used (cm).</li>
    </ul>
    
    <p><strong>Step 3:</strong></p>
    <ul>
        <li>Select whether you want to crochet the whole globe at once or the northern and southern hemisphere separately. Enter all measurements and click <strong>"GENERATE"</strong>. Depending on the selected size, it may take a few minutes until the crochet pattern and the expected yarn consumption will appear. Note that color changes also require yarn and thus expect a higher yarn consumption depending on the resolution of the globe.</li>
    </ul>

    <p><strong>Step 4:</strong></p>
    <ul>
        <li>Either crochet the entire globe as a single piece and stuff it immediately or or crochet the northern and southern hemispheres separately and join them at the equator. If the globe is used as a pillow case, you may use a red zipper to mark the equator.</li>
    </ul>


    <p><strong>Abbreviations:</strong></p>
    <ul>
        <li><strong>sc</strong> = single crochet, <strong>inc</strong> = increase, <strong>dec</strong> = decrease</li>
    </ul>
</div>

           

        </div>
      

      <div className="flex flex-col md:flex-row md:items-start gap-6 pt-15"> {/*unterer abschnitt*/}

        {/* Parameter Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 flex-1 pr-10">
          {Object.entries(parameterConfig).map(([key, config]) => (
            <ParameterInput
              key={key}
              name={key}
              value={params[key]}
              config={config}
              onChange={updateParam}
            />
          ))}
          <button
          onClick={run}
          className="w-full px-4 py-2 bg-red-900 text-white rounded hover:bg-red-400 transition-colors"
        >
          GENERATE
        </button>
        </div>

        

      

       {/* <div className="flex justify-center items-center mt-5 ">
      <div className="flex justify-center mt-5 w-1/3">
        <button
          onClick={run}
          className="px-10 py-6 bg-red-900 text-white rounded hover:bg-red-400 transition-colors"
        >
          GENERATE
        </button>
      </div>

</div>*/}

      {markers.length === 0 ? (
        <p className="text-gray-600 text-center flex-1">No Data.</p>
      ) : (
        <div className="flex flex-col items-center gap-4 flex-1">
          <h2 className="text-2xl font-semibold text-center">Pattern</h2>
          <div className="flex items-center gap-4 w-full max-w-xxl">

            <button
              onClick={prev}
              disabled={index === 0}
              className="px-3 py-2 bg-gray-200 rounded disabled:opacity-40 hover:bg-gray-300 transition-colors"
            >
              ←
            </button>

            <pre className="bg-white p-4 rounded overflow-auto whitespace-pre-wrap flex-grow shadow">
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



      <div className="flex-1">
      <table className="text-sm w-full">
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
    </div>
  );
}
