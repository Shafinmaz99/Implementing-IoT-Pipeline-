import React, { useEffect, useState } from "react";
import "./App.css";

function Cell({ value, isPath, isStart, isTarget }) {
  let className = "cell";

  if (value === 1) className += " blocked";
  else if (value === 2) className += " narrow";
  else className += " walkable";

  if (isPath) className += " path";
  if (isStart) className += " start";
  if (isTarget) className += " target";

  let label = "";
  if (isStart) label = "S";
  else if (isTarget) label = "T";

  return <div className={className}>{label}</div>;
}

function App() {
  const [modeType, setModeType] = useState("single");
  const [productId, setProductId] = useState("C1");
  const [multiProducts, setMultiProducts] = useState(["C1", "C2"]);
  const [singleMode, setSingleMode] = useState("smart");
  const [data, setData] = useState(null);

  useEffect(() => {
    let url = "";

    if (modeType === "single") {
      url = `http://127.0.0.1:8000/dashboard?product_id=${productId}&mode=${singleMode}`;
    } else {
      url = `http://127.0.0.1:8000/multi-dashboard?product_ids=${multiProducts.join(",")}`;
    }

    setData(null);

    fetch(url)
      .then((response) => response.json())
      .then((json) => setData(json))
      .catch((error) => {
        console.error("Error fetching data:", error);
        setData({ error: "Failed to load dashboard data." });
      });
  }, [modeType, productId, singleMode, multiProducts]);

  const handleMultiProductChange = (id) => {
    setMultiProducts((prev) => {
      if (prev.includes(id)) {
        if (prev.length <= 2) return prev;
        return prev.filter((item) => item !== id);
      } else {
        if (prev.length >= 4) return prev;
        return [...prev, id];
      }
    });
  };

  if (!data) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (data.error) {
    return <div className="loading">{data.error}</div>;
  }

  const grid = data?.warehouse?.grid || [];
  const start = data?.warehouse?.start_position || [0, 0];

  let path = [];
  let targetPositions = [];

  if (modeType === "single") {
    path = data?.active_route?.result?.path || [];
    targetPositions = data?.selected_product?.location
      ? [data.selected_product.location]
      : [];
  } else {
    path = data?.smart_multi_route?.combined_path || [];
    targetPositions = data?.selected_products?.map((p) => p.location) || [];
  }

  const pathSet = new Set(path.map((pos) => `${pos[0]}-${pos[1]}`));
  const targetSet = new Set(targetPositions.map((pos) => `${pos[0]}-${pos[1]}`));

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Smart Warehouse Analytics Dashboard</h1>
          <p>Lindström Carpet Warehouse</p>
        </div>

        <div className="controls vertical">
          <select value={modeType} onChange={(e) => setModeType(e.target.value)}>
            <option value="single">Single Item</option>
            <option value="multi">Multi Item Picking</option>
          </select>

          {modeType === "single" && (
            <>
              <select value={productId} onChange={(e) => setProductId(e.target.value)}>
                {(data.products || []).map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.name}
                  </option>
                ))}
              </select>

              <select value={singleMode} onChange={(e) => setSingleMode(e.target.value)}>
                <option value="basic">Basic Route</option>
                <option value="smart">Smart Route</option>
              </select>
            </>
          )}
        </div>
      </header>

      {modeType === "multi" && (
        <div className="card multi-select-card">
          <h2>Select 2 to 4 Carpets</h2>
          <div className="checkbox-row">
            {(data.products || []).map((product) => (
              <label key={product.id} className="checkbox-item">
                <input
                  type="checkbox"
                  checked={multiProducts.includes(product.id)}
                  onChange={() => handleMultiProductChange(product.id)}
                />
                {product.name}
              </label>
            ))}
          </div>
        </div>
      )}

      <div className="dashboard">
        <div className="main-column">
          <div className="card">
            <h2>Warehouse Route Map</h2>

            <div className="grid">
              {grid.map((row, rowIndex) =>
                row.map((cell, colIndex) => {
                  const key = `${rowIndex}-${colIndex}`;
                  const isPath = pathSet.has(key);
                  const isStart = start[0] === rowIndex && start[1] === colIndex;
                  const isTarget = targetSet.has(key);

                  return (
                    <Cell
                      key={key}
                      value={cell}
                      isPath={isPath}
                      isStart={isStart}
                      isTarget={isTarget}
                    />
                  );
                })
              )}
            </div>

            <div className="legend">
              <span><span className="legend-box walkable"></span> Walkable</span>
              <span><span className="legend-box blocked"></span> Shelf</span>
              <span><span className="legend-box narrow"></span> Narrow Path</span>
              <span><span className="legend-box path-outline"></span> Active Route</span>
            </div>
          </div>
        </div>

        <div className="side-column">
          {modeType === "single" ? (
            <>
              <div className="card">
                <h2>Selected Product</h2>
                <p><strong>Name:</strong> {data?.selected_product?.name || "-"}</p>
                <p><strong>Weight:</strong> {data?.selected_product?.weight ?? "-"} kg</p>
                <p>
                  <strong>Location:</strong>{" "}
                  {data?.selected_product?.location
                    ? `(${data.selected_product.location[0]}, ${data.selected_product.location[1]})`
                    : "-"}
                </p>
              </div>

              <div className="card">
                <h2>Active Route Metrics</h2>
                <div className="metric-list">
                  <div className="metric-item"><span>Cost</span><strong>{data?.active_route?.result?.total_cost ?? "-"}</strong></div>
                  <div className="metric-item"><span>Steps</span><strong>{data?.active_route?.result?.steps ?? "-"}</strong></div>
                  <div className="metric-item"><span>Time</span><strong>{data?.active_route?.analytics?.estimated_time_minutes ?? "-"} min</strong></div>
                  <div className="metric-item"><span>Fatigue</span><strong>{data?.active_route?.analytics?.fatigue_level ?? "-"}</strong></div>
                  <div className="metric-item"><span>Efficiency</span><strong>{data?.active_route?.analytics?.efficiency_score ?? "-"}</strong></div>
                  <div className="metric-item"><span>Safety</span><strong>{data?.active_route?.analytics?.safety_score ?? "-"}</strong></div>
                </div>
              </div>

              <div className="card">
                <h2>Comparison</h2>
                <div className="metric-list">
                  <div className="metric-item"><span>Basic Cost</span><strong>{data?.comparison?.basic_cost ?? "-"}</strong></div>
                  <div className="metric-item"><span>Smart Cost</span><strong>{data?.comparison?.smart_cost ?? "-"}</strong></div>
                  <div className="metric-item"><span>Cost Difference</span><strong>{data?.comparison?.cost_difference ?? "-"}</strong></div>
                  <div className="metric-item"><span>Basic Fatigue</span><strong>{data?.comparison?.basic_fatigue ?? "-"}</strong></div>
                  <div className="metric-item"><span>Smart Fatigue</span><strong>{data?.comparison?.smart_fatigue ?? "-"}</strong></div>
                  <div className="metric-item"><span>Fatigue Difference</span><strong>{data?.comparison?.fatigue_difference ?? "-"}</strong></div>
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="card">
                <h2>Selected Carpets</h2>
                {(data?.selected_products || []).map((product) => (
                  <p key={product.id}>
                    <strong>{product.name}</strong> - {product.weight} kg
                  </p>
                ))}
              </div>

              <div className="card">
                <h2>Visit Order</h2>
                {(data?.smart_multi_route?.visit_order || []).map((product, index) => (
                  <p key={product.id}>
                    {index + 1}. {product.name} ({product.location[0]}, {product.location[1]})
                  </p>
                ))}
              </div>

              <div className="card">
                <h2>Return to Base</h2>
                <p><strong>Return Enabled:</strong> {data?.smart_multi_route?.return_to_base ? "Yes" : "No"}</p>
                <p>
                  <strong>Base Position:</strong>{" "}
                  {data?.smart_multi_route?.base_position
                    ? `(${data.smart_multi_route.base_position[0]}, ${data.smart_multi_route.base_position[1]})`
                    : "-"}
                </p>
              </div>

              <div className="card">
                <h2>Combined Analytics</h2>
                <div className="metric-list">
                  <div className="metric-item">
                    <span>Smart Total Cost</span>
                    <strong>{data?.smart_multi_route?.total_cost ?? "-"}</strong>
                  </div>
                  <div className="metric-item">
                    <span>Steps</span>
                    <strong>{data?.smart_multi_route?.analytics?.steps ?? "-"}</strong>
                  </div>
                  <div className="metric-item">
                    <span>Time</span>
                    <strong>{data?.smart_multi_route?.analytics?.estimated_time_minutes ?? "-"} min</strong>
                  </div>
                  <div className="metric-item">
                    <span>Fatigue</span>
                    <strong>{data?.smart_multi_route?.analytics?.fatigue_level ?? "-"}</strong>
                  </div>
                  <div className="metric-item">
                    <span>Total Weight</span>
                    <strong>{data?.smart_multi_route?.analytics?.total_weight ?? "-"} kg</strong>
                  </div>
                </div>
              </div>

              <div className="card">
                <h2>Comparison</h2>
                <div className="metric-list">
                  <div className="metric-item"><span>Basic Cost</span><strong>{data?.comparison?.basic_cost ?? "-"}</strong></div>
                  <div className="metric-item"><span>Smart Cost</span><strong>{data?.comparison?.smart_cost ?? "-"}</strong></div>
                  <div className="metric-item"><span>Cost Difference</span><strong>{data?.comparison?.cost_difference ?? "-"}</strong></div>
                  <div className="metric-item"><span>Basic Fatigue</span><strong>{data?.comparison?.basic_fatigue ?? "-"}</strong></div>
                  <div className="metric-item"><span>Smart Fatigue</span><strong>{data?.comparison?.smart_fatigue ?? "-"}</strong></div>
                  <div className="metric-item"><span>Fatigue Difference</span><strong>{data?.comparison?.fatigue_difference ?? "-"}</strong></div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;