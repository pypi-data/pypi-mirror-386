import type { Meta, StoryObj } from "@storybook/react-vite";
import { http, HttpResponse, delay } from "msw";

import DisplayComments from "./DisplayComments";

const meta = {
  component: DisplayComments,
} satisfies Meta<typeof DisplayComments>;

export default meta;
type Story = StoryObj<typeof meta>;

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
          return new HttpResponse(null, {
            status: 404,
          });
        }),
      ],
    },
  },
};
