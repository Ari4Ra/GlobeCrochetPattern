import React, { useState, useEffect } from 'react';
import { generate, API } from './api';
import { MapContainer, TileLayer, CircleMarker } from "react-leaflet";

export default function App() {
  const [params, setParams] = useState({
    stitchlength: 2,
    stitchheight: 2,
    stitchsetback: 1,
    diametercm: 1,
    amountofteststitches:100,
    lengthoftestyarn: 3,
  });
const paramLabels = {
    stitchlength: "Stitch Length (mm)",
    stitchheight: "Stitch Height (mm)",
    stitchsetback: "Stitch Setback (mm)",
    diametercm: "Globe Diameter (cm)",
    amountofteststitches: "Amount of Test Stitches",
    lengthoftestyarn: "Length of Test Yarn",
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
    <div className="p-6 relative min-h-screen bg-gray-50">
      <h1 className="text-3xl font-bold mb-6 text-center">Globe Crochet Pattern Generator</h1>

     <div className="flex flex-col md:flex-row md:items-start gap-6">
  {/* Instructions box */}
  <div className="bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800 p-4 rounded max-w-xs md:max-w-sm">
    <h3 className="font-semibold mb-2">Instruction</h3>
    <p>
     At first crochet a small test circle, eg. start with 6 sc and increase 6 in each row.
     Then measure the height and width of each stitch in mm. Furthermore, you will notice that the stiches
     do not sit exactly on top of each other. Measure the setback that occurs in each row in mm. Count the amount of
     stitches, unravel and measure the length of the yarn you needed in cm. Enter the data and klick "GENERATE".
     The pattern and the amount of yarn you need of each color will appear. Here "sc" means single crochet,
     "inc" means increase and "dec" means decrease.
    </p>
  </div>

  {/* Parameter Grid */}
  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
    {Object.keys(params).map(key => (
      <label key={key} className="flex flex-col text-sm font-medium">
        {paramLabels[key]}:
        <input
          type="number"
          min="0"
          step="0.1"
          value={params[key]}
          onChange={e => setParams({ ...params, [key]: Number(e.target.value) })}
          className="mt-1 border rounded px-2 py-1 text-sm focus:outline-none focus:ring focus:ring-blue-300"
        />
      </label>
    ))}
  </div>
</div>


      <div className="flex justify-center mt-5">
        <button
          onClick={run}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          GENERATE
        </button>
      </div>


      <h2 className="text-2xl font-semibold mt-8 text-center">Pattern</h2>

      {markers.length === 0 ? (
        <p className="text-gray-600 mt-2 text-center">No Data.</p>
      ) : (
        <div className="mt-4 flex flex-col items-center gap-4">
          <div className="flex items-center gap-4 w-full max-w-xl">
            {/* ← Pfeil */}
            <button
              onClick={prev}
              disabled={index === 0}
              className="px-3 py-2 bg-gray-200 rounded disabled:opacity-40 hover:bg-gray-300 transition-colors"
            >
              ←
            </button>

            {/* Ausgabe Box */}
            <pre className="bg-white p-4 rounded max-h-72 overflow-auto whitespace-pre-wrap flex-grow shadow">
              {formatMarker(current).map((line, i) => (
                <div key={i}>{line}</div>
              ))}
            </pre>

            {/* → Pfeil */}
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

<table className="w-full text-sm">
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
  );
}

