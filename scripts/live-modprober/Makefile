#* ************************************************************************** *#
#*                                                                            *#
#*                                                        :::      ::::::::   *#
#*   Makefile                                           :+:      :+:    :+:   *#
#*                                                    +:+ +:+         +:+     *#
#*   By: snicolet <marvin@student.42.fr>            +#+  +:+       +#+        *#
#*                                                +#+#+#+#+#+   +#+           *#
#*   Created: 2019/05/07 11:57:08 by snicolet          #+#    #+#             *#
#*   Updated: 2019/05/07 11:59:52 by snicolet         ###   ########.fr       *#
#*                                                                            *#
#* ************************************************************************** *#

install:
	sudo cp -v ./live-prober.service /etc/systemd/system/
	sudo cp -v ./live-modprober.py /usr/bin/
	sudo chmod 700 /usr/bin/live-modprober.py
	sudo systemctl enable live-prober.service

uninstall:
	sudo systemctl disable live-prober.service || true
	sudo rm -f /etc/systemd/live-modprober.service /usr/bin/live-modprober.py

