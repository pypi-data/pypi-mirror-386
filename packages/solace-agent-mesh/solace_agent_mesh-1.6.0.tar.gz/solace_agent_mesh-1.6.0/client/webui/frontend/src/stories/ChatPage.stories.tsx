import type { Meta, StoryContext, StoryFn, StoryObj } from "@storybook/react-vite";
import { mockMessages, mockLoadingMessage } from "./mocks/data";
import { ChatPage } from "@/lib/components/pages/ChatPage";
import { screen, within } from "storybook/test";

const meta = {
    title: "Pages/ChatPage",
    component: ChatPage,
    parameters: {
        layout: "fullscreen",
        docs: {
            description: {
                component: "The main chat page component that displays the chat interface, side panels, and handles user interactions.",
            },
        },
    },
    decorators: [
        (Story: StoryFn, context: StoryContext) => {
            const storyResult = Story(context.args, context);

            return <div style={{ height: "100vh", width: "100vw" }}>{storyResult}</div>;
        },
    ],
} satisfies Meta<typeof ChatPage>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    parameters: {
        chatContext: {
            sessionId: "mock-session-id",
            messages: mockMessages,
            userInput: "",
            isResponding: false,
            isCancelling: false,
            selectedAgentName: "OrchestratorAgent",
            isSidePanelCollapsed: true,
            activeSidePanelTab: "files",
        },
        configContext: {
            persistenceEnabled: false,
        },
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);

        await canvas.findByTestId("expandPanel");
        await canvas.findByTestId("sendMessage");
    },
};

export const WithLoadingMessage: Story = {
    parameters: {
        chatContext: {
            sessionId: "mock-session-id",
            messages: [...mockMessages, mockLoadingMessage],
            userInput: "",
            isResponding: true,
            isCancelling: false,
            selectedAgentName: "OrchestratorAgent",
            isSidePanelCollapsed: true,
            activeSidePanelTab: "files",
        },
        configContext: {
            persistenceEnabled: false,
        },
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);

        await canvas.findByTestId("expandPanel");
        await canvas.findByTestId("viewAgentWorkflow");
        await canvas.findByTestId("cancel");
    },
};

export const WithSidePanelOpen: Story = {
    parameters: {
        chatContext: {
            sessionId: "mock-session-id",
            messages: mockMessages,
            userInput: "",
            isResponding: false,
            isCancelling: false,
            selectedAgentName: "OrchestratorAgent",
            isSidePanelCollapsed: true,
            isSidePanelTransitioning: false,
            activeSidePanelTab: "files",
            artifacts: [],
            artifactsLoading: false,
        },
        configContext: {
            persistenceEnabled: false,
        },
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);

        // Open side panel to trigger resize of panel
        const openRightSidePanel = await canvas.findByTestId("expandPanel");
        openRightSidePanel.click();

        await canvas.findByTestId("collapsePanel");
        await canvas.findByText("No files available");
    },
};

export const NewSessionDialog: Story = {
    parameters: {
        chatContext: {
            sessionId: "mock-session-id",
            messages: mockMessages,
            userInput: "",
            isResponding: false,
            isCancelling: false,
            selectedAgentName: "OrchestratorAgent",
            isSidePanelCollapsed: true,
            isSidePanelTransitioning: false,
            activeSidePanelTab: "files",
            artifacts: [],
            artifactsLoading: false,
        },
        configContext: {
            persistenceEnabled: false,
        },
    },

    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);

        // Open side panel to trigger resize of panel
        const openLeftSidePanel = await canvas.findByTestId("showSessionsPanel");
        openLeftSidePanel.click();

        await canvas.findByTestId("hideChatSessions");

        // Open chat session dialog
        const startNewChatSessionButton = await canvas.findByTestId("startNewChat");
        startNewChatSessionButton.click();

        // Verify dialog
        await screen.findByRole("dialog");
        await screen.findByRole("button", { name: "Start New Chat" });
    },
};
