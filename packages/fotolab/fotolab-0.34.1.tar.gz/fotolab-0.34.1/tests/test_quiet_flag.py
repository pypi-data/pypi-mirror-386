# Copyright (C) 2024,2025 Kian-Meng Ang

# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import pytest


@pytest.mark.parametrize("option", ["-q", "--quiet"])
def test_no_debug_logs(cli_runner, option):
    ret = cli_runner(option)
    assert "debug=True" not in ret.stderr
