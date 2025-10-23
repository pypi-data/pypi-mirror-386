import type { Meta, StoryObj } from "@storybook/react-vite";
import { http, HttpResponse, delay } from "msw";

import DisplayComments from "./DisplayComments";

const meta = {
  component: DisplayComments,
} satisfies Meta<typeof DisplayComments>;

export default meta;
type Story = StoryObj<typeof meta>;

const data = {
  comments: [],
  sharedBy: [],
  likedBy: [],
  rootUri:
    "https://comments.bovine.social/pages/aHR0cHM6Ly9oZWxnZS5jb2RlYmVyZy5wYWdlL21rZG9jc19mZWRpX2NvbW1lbnRzLw==",
};

export const NotFoundError: Story = {
  args: {
    baseUrl: "https://endpoint",
    encodedUrl: "something",
  },
  parameters: {
    msw: {
      handlers: [
        http.get("https://endpoint/something", async () => {
          await delay(800);
          return HttpResponse.json(data);
        }),
      ],
    },
  },
};
