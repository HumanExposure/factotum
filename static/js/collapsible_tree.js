/**
 * D3 Collapsible Tree.
 *
 * For more information, see: https://observablehq.com/@d3/collapsible-tree?collection=@d3/d3-hierarchy.
 *
 * @param {string}  dataurl                                                 Url to populate collapsible tree.
 * @param {int}     [width=1140]                                            Estimated width of collapsible tree
 * @param {int}     [dx=18]                                                 Distance between nodes vertically
 * @param {int}     [dy=228]                                                Distance between nodes horizontally (width/5)
 * @param {Object}  [margin=({top:10, right:120, bottom:10, left:120})]     Internal margins for first nodes
 *
 * @return Void 
 */
function collapsibleTree(dataurl, width = 1140, dx = 18, dy = 228, margin = ({
    top: 10,
    right: 40,
    bottom: 10,
    left: 120
})) {
    d3v5.json(dataurl)
        .then(function (data) {
            const root = d3v5.hierarchy(data);

            diagonal = d3v5.linkHorizontal().x(d => d.y).y(d => d.x)
            tree = d3v5.tree().nodeSize([dx, dy])

            root.x0 = dy / 2;
            root.y0 = 0;
            root.descendants().forEach((d, i) => {
                d.id = i;
                d._children = d.children;
                if (d.depth) d.children = null; // Only open one layer deep
            });

            const svg = d3v5.select("#collapsibletree")
                .attr("viewBox", [-margin.left, -margin.top, width, dx])
                .style("font", "14px sans-serif")
                .style("user-select", "none");

            const gLink = svg.append("g")
                .attr("fill", "none")
                .attr("stroke", "#555")
                .attr("stroke-opacity", 0.4)
                .attr("stroke-width", 1.5);

            const gNode = svg.append("g")
                .attr("cursor", "pointer")
                .attr("pointer-events", "all");

            function update(source) {
                const duration = d3v5.event && d3v5.event.altKey ? 2500 : 250;
                const nodes = root.descendants().reverse();
                const links = root.links();

                // Compute the new tree layout.
                tree(root);

                let left = root;
                let right = root;
                root.eachBefore(node => {
                    if (node.x < left.x) left = node;
                    if (node.x > right.x) right = node;
                });

                const height = right.x - left.x + margin.top + margin.bottom;

                const transition = svg.transition()
                    .duration(duration)
                    .attr("viewBox", [-margin.left, left.x - margin.top, width, height])
                    .tween("resize", window.ResizeObserver ? null : () => () => svg.dispatch("toggle"));

                // Update the nodes…
                const node = gNode.selectAll("g")
                    .data(nodes, d => d.id);

                // Enter any new nodes at the parent's previous position.
                const nodeEnter = node.enter().append("g")
                    .attr("transform", d => `translate(${source.y0},${source.x0})`)
                    .attr("fill-opacity", 0)
                    .attr("stroke-opacity", 0);

                nodeEnter.append("circle")
                    .attr("r", 2.5)
                    .attr("fill", d => d._children ? "#555" : "#999")
                    .attr("stroke-width", 10)
                    .attr("class", "tree-node")
                    .on("click", d => {
                        d.children = d.children ? null : d._children;
                        update(d);
                    });

                nodeEnter.append("text")
                    .attr("dy", "0.31em")
                    .attr("x", d => d._children ? -6 : 6)
                    .attr("text-anchor", d => d._children ? "end" : "start")
                    .text(d => d.data.name)
                    .on("click", d => {
                        if (d.data.value.id) {
                            window.location.assign('/puc/' + d.data.value.id);
                        }
                    })
                    .clone(true).lower()
                    .attr("stroke-linejoin", "round")
                    .attr("stroke-width", 3)
                    .attr("stroke", "white");

                // Transition nodes to their new position.
                const nodeUpdate = node.merge(nodeEnter).transition(transition)
                    .attr("transform", d => `translate(${d.y},${d.x})`)
                    .attr("fill-opacity", 1)
                    .attr("stroke-opacity", 1);

                // Transition exiting nodes to the parent's new position.
                const nodeExit = node.exit().transition(transition).remove()
                    .attr("transform", d => `translate(${source.y},${source.x})`)
                    .attr("fill-opacity", 0)
                    .attr("stroke-opacity", 0);

                // Update the links…
                const link = gLink.selectAll("path")
                    .data(links, d => d.target.id);

                // Enter any new links at the parent's previous position.
                const linkEnter = link.enter().append("path")
                    .attr("d", d => {
                        const o = {
                            x: source.x0,
                            y: source.y0
                        };
                        return diagonal({
                            source: o,
                            target: o
                        });
                    });

                // Transition links to their new position.
                link.merge(linkEnter).transition(transition)
                    .attr("d", diagonal);

                // Transition exiting nodes to the parent's new position.
                link.exit().transition(transition).remove()
                    .attr("d", d => {
                        const o = {
                            x: source.x,
                            y: source.y
                        };
                        return diagonal({
                            source: o,
                            target: o
                        });
                    });

                // Stash the old positions for transition.
                root.eachBefore(d => {
                    d.x0 = d.x;
                    d.y0 = d.y;
                });
            }

            update(root);

            return svg.node();
        })
        .catch(console.log.bind(console));
}