import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { crearCliente } from "@/shared/api";
import { App } from "./App";

// El unico sitio que da el fetch real al cliente; el resto de la app no lo ve.
const cliente = crearCliente(window.fetch.bind(window));

createRoot(document.getElementById("raiz")!).render(
  <StrictMode>
    <App cliente={cliente} />
  </StrictMode>,
);
