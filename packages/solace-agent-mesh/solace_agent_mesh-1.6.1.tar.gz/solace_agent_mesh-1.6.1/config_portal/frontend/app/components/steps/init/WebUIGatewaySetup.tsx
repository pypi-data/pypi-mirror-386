import { useState, useEffect } from "react";
import FormField from "../../ui/FormField";
import Input from "../../ui/Input";
import Checkbox from "../../ui/Checkbox";
import Button from "../../ui/Button";
import { InfoBox } from "../../ui/InfoBoxes";
import { StepComponentProps } from "../../InitializationFlow";

interface WebUIGatewayData {
  add_webui_gateway?: boolean;
  webui_session_secret_key?: string;
  webui_fastapi_host?: string;
  webui_fastapi_port?: number;
  webui_enable_embed_resolution?: boolean;
  webui_frontend_welcome_message?: string;
  webui_frontend_bot_name?: string;
  webui_frontend_collect_feedback?: boolean;
  database_url?: string;
  [key: string]: string | number | boolean | undefined;
}

export default function WebUIGatewaySetup({
  data,
  updateData,
  onNext,
  onPrevious,
}: StepComponentProps) {
  const [errors, setErrors] = useState<Record<string, string>>({});
  const webUiGatewayData = data as WebUIGatewayData;

  useEffect(() => {
    const defaults: Partial<WebUIGatewayData> = {
      add_webui_gateway: webUiGatewayData.add_webui_gateway ?? false,
      webui_session_secret_key: webUiGatewayData.webui_session_secret_key ?? "",
      webui_fastapi_host: webUiGatewayData.webui_fastapi_host ?? "127.0.0.1",
      webui_fastapi_port: webUiGatewayData.webui_fastapi_port ?? 8000,
      webui_enable_embed_resolution: webUiGatewayData.webui_enable_embed_resolution ?? true,
      webui_frontend_welcome_message: webUiGatewayData.webui_frontend_welcome_message ?? "",
      webui_frontend_bot_name:
        webUiGatewayData.webui_frontend_bot_name ?? "Solace Agent Mesh",
      webui_frontend_collect_feedback:
        webUiGatewayData.webui_frontend_collect_feedback ?? false,
    };

    const updatesNeeded: Partial<WebUIGatewayData> = {};
    for (const key in defaults) {
      if (
        webUiGatewayData[key] === undefined &&
        defaults[key as keyof typeof defaults] !== undefined
      ) {
        updatesNeeded[key as keyof WebUIGatewayData] =
          defaults[key as keyof typeof defaults];
      }
    }
    if (Object.keys(updatesNeeded).length > 0) {
      updateData(updatesNeeded);
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    if (type === "number") {
      updateData({ [name]: value === "" ? "" : Number(value) });
    } else {
      updateData({ [name]: value });
    }
  };

  const handleCheckboxChange = (
    name: keyof WebUIGatewayData,
    checked: boolean
  ) => {
    updateData({ [name]: checked });
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    let isValid = true;

    if (webUiGatewayData.add_webui_gateway) {
      if (!webUiGatewayData.webui_session_secret_key) {
        newErrors.webui_session_secret_key = "Session Secret Key is required.";
        isValid = false;
      }
      if (!webUiGatewayData.webui_fastapi_host) {
        newErrors.webui_fastapi_host = "FastAPI Host is required.";
        isValid = false;
      }
      if (
        webUiGatewayData.webui_fastapi_port === undefined 
      ) {
        newErrors.webui_fastapi_port = "FastAPI Port is required.";
        isValid = false;
      } else if (
        isNaN(Number(webUiGatewayData.webui_fastapi_port)) ||
        Number(webUiGatewayData.webui_fastapi_port) <= 0
      ) {
        newErrors.webui_fastapi_port =
          "FastAPI Port must be a positive number.";
        isValid = false;
      }
    }
    setErrors(newErrors);
    return isValid;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onNext();
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="space-y-6">
        <InfoBox className="mb-4">
          Optionally, configure a Web UI Gateway to interact with your Solace
          Agent Mesh. This provides a Web UI chat interface.
        </InfoBox>

        <FormField label="" htmlFor="add_webui_gateway">
          <Checkbox
            id="add_webui_gateway"
            checked={webUiGatewayData.add_webui_gateway || false}
            onChange={(checked) =>
              handleCheckboxChange("add_webui_gateway", checked)
            }
            label="Add Web UI Gateway"
          />
        </FormField>

        {webUiGatewayData.add_webui_gateway && (
          <div className="space-y-4 p-4 border border-gray-200 rounded-md mt-4">
            <h3 className="text-md font-medium text-gray-800 mb-3">
              Web UI Gateway Configuration
            </h3>
            <FormField
              label="Session Secret Key"
              htmlFor="webui_session_secret_key"
              error={errors.webui_session_secret_key}
              required
            >
              <Input
                id="webui_session_secret_key"
                name="webui_session_secret_key"
                type="password"
                value={webUiGatewayData.webui_session_secret_key || ""}
                onChange={handleChange}
                placeholder="Enter a strong secret key"
              />
            </FormField>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                label="FastAPI Host"
                htmlFor="webui_fastapi_host"
                error={errors.webui_fastapi_host}
                required
              >
                <Input
                  id="webui_fastapi_host"
                  name="webui_fastapi_host"
                  value={webUiGatewayData.webui_fastapi_host || "127.0.0.1"}
                  onChange={handleChange}
                  placeholder="127.0.0.1"
                />
              </FormField>

              <FormField
                label="FastAPI Port"
                htmlFor="webui_fastapi_port"
                error={errors.webui_fastapi_port}
                required
              >
                <Input
                  id="webui_fastapi_port"
                  name="webui_fastapi_port"
                  type="number"
                  value={
                    webUiGatewayData.webui_fastapi_port === undefined
                      ? ""
                      : String(webUiGatewayData.webui_fastapi_port)
                  }
                  onChange={handleChange}
                  placeholder="8000"
                />
              </FormField>
            </div>

            <FormField label="" htmlFor="webui_enable_embed_resolution">
              <Checkbox
                id="webui_enable_embed_resolution"
                checked={webUiGatewayData.webui_enable_embed_resolution || false}
                onChange={(checked) =>
                  handleCheckboxChange("webui_enable_embed_resolution", checked)
                }
                label="Enable Embed Resolution in Web UI"
              />
            </FormField>

            <h4 className="text-sm font-medium text-gray-700 mt-3 mb-2">
              Frontend Customization
            </h4>
            <FormField
              label="Frontend Welcome Message"
              htmlFor="webui_frontend_welcome_message"
              error={errors.webui_frontend_welcome_message}
            >
              <Input
                id="webui_frontend_welcome_message"
                name="webui_frontend_welcome_message"
                value={webUiGatewayData.webui_frontend_welcome_message || ""}
                onChange={handleChange}
                placeholder="Welcome to the Solace Agent Mesh!"
              />
            </FormField>

            <FormField
              label="Frontend Bot Name"
              htmlFor="webui_frontend_bot_name"
              error={errors.webui_frontend_bot_name}
            >
              <Input
                id="webui_frontend_bot_name"
                name="webui_frontend_bot_name"
                value={webUiGatewayData.webui_frontend_bot_name || "Solace Agent Mesh"}
                onChange={handleChange}
                placeholder="Solace Agent Mesh"
              />
            </FormField>

            <FormField label="" htmlFor="webui_frontend_collect_feedback">
              <Checkbox
                id="webui_frontend_collect_feedback"
                checked={webUiGatewayData.webui_frontend_collect_feedback || false}
                onChange={(checked) =>
                  handleCheckboxChange(
                    "webui_frontend_collect_feedback",
                    checked
                  )
                }
                label="Enable Feedback Collection in Frontend"
              />
            </FormField>

            {/* eslint-disable-next-line */}
            {/* <h4 className="text-sm font-medium text-gray-700 mt-3 mb-2">
              Database Configuration
            </h4>
            <InfoBox className="mb-4">
              A local SQLite database will be created for your Web UI Gateway to store chat
              history and session data. You can override this by providing a
              connection string to a different database.
            </InfoBox>
            <FormField
              label="Database URL"
              htmlFor="database_url"
              helpText="Leave blank to use the default SQLite database."
            >
              <Input
                id="database_url"
                name="database_url"
                value={webUiGatewayData.database_url || ""}
                onChange={handleChange}
                placeholder="e.g., sqlite:///gatewayDatabase.db"
              />
            </FormField> */}
          </div>
        )}
      </div>

      <div className="mt-8 flex justify-end space-x-4">
        <Button onClick={onPrevious} variant="outline" type="button">
          Previous
        </Button>
        <Button type="submit">Next</Button>
      </div>
    </form>
  );
}
