import React from "react";
import ReactDOM from "react-dom/client";
import { pdfjs } from "react-pdf";
import workerUrl from "pdfjs-dist/build/pdf.worker.min.mjs?url";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

import App from "./App.jsx";
import "./styles.css";

pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
