import React from "react";
import { Switch, Route, Link } from "react-router-dom";
import { Button, Icon, Menu, Segment } from "semantic-ui-react";
import "./style.css";
import { Header } from "./Header";

export function Settings() {
  return (
    <div>
      <Header>Stepper Motors</Header>

      <p>Stepper Motors</p>
    </div>
  );
}
